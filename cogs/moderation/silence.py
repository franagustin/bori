import dataclasses
from datetime import timedelta
from typing import Tuple

from bori_models.models import MutedMember
from discord import Embed, Guild, Member, PermissionOverwrite, Role, utils
from discord.errors import Forbidden
from discord.ext.commands import (
    Bot, Cog, command, Context, guild_only, has_permissions, RoleConverter
)
from pytz import utc

from utils.guild_utils import get_author_string, role_exists


DEFAULT_MUTED_ROLE_NAME = '[BORI-GHOST] Muted'
DEFAULT_REASON = 'No se ha especificado una razón.'
MUTED_PERMISSIONS = PermissionOverwrite(send_messages=False, add_reactions=False)

@dataclasses.dataclass(eq=False)
class Silence(Cog):
    bot: Bot

    @guild_only()
    @has_permissions(manage_roles=True)
    @command(name='muted-role', aliases=['mute-role', 'silenced-role', 'silence-role'])
    async def set_muted_role(self, ctx: Context, *, role: Role = None):
        role = role or await self.get_muted_role(ctx)
        settings = await self._get_settings(ctx)
        settings.muted_role = role.id
        self.bot.cache.set('muted_role', ctx.message.guild.id, role.id)
        await self.bot.db.guild_settings.find_one_and_update(
            {'guild_id': settings.guild_id},
            {'$set': settings.to_primitive()}
        )
        await ctx.message.channel.send(f'El nuevo rol silenciado es {role.name}')

    @guild_only()
    @has_permissions(manage_roles=True)
    @command(name='mute', aliases=['silence', 'mutear', 'mutea', 'silenciar', 'silencia'])
    async def mute(self, ctx: Context, member: Member, *, reason: str = None):
        # TODO: Add time parameter
        # TODO: Save in database
        reason = reason or DEFAULT_REASON
        muted_role = await self.get_muted_role(ctx)
        try:
            muted_role = await RoleConverter().convert(ctx, str(muted_role))
        except ValueError:
            await ctx.message.channel.send('Rol silenciado inválido.')
            return
        await member.add_roles(muted_role, reason=reason)
        await self.register_mute_on_db(ctx, member)
        embeds = await self._build_embed(ctx, member, reason)
        await self._send_messages(ctx, member, embeds)

    async def get_muted_role(self, ctx: Context):
        guild = ctx.message.guild
        muted_role = self.bot.cache.get('muted_role', guild.id)
        if muted_role is None:
            settings = await self._get_settings(ctx)
            muted_role = settings.muted_role
        if muted_role is None or not role_exists(guild.roles, int(muted_role)):
            muted_role = await self.get_default_muted_role(guild)
        muted_role = await RoleConverter().convert(ctx, muted_role)
        return muted_role

    async def get_default_muted_role(self, guild: Guild):
        muted_role = utils.get(guild.roles, name=DEFAULT_MUTED_ROLE_NAME)
        if muted_role is None:
            muted_role = await self.create_muted_role(guild)
        return muted_role

    async def create_muted_role(self, guild: Guild):
        muted_role = await guild.create_role(name=DEFAULT_MUTED_ROLE_NAME)
        for channel in guild.text_channels:
            await channel.edit(overwrites={muted_role: MUTED_PERMISSIONS})
        muted_role = muted_role.id
        self.bot.cache.set('muted_role', guild.id, muted_role)
        return muted_role

    async def register_mute_on_db(self, ctx: Context, member: Member):
        start_time = utc.localize(ctx.message.created_at)
        muted_member = MutedMember({
            'guild_id': ctx.message.guild.id,
            'user_id': member.id,
            'start_time': start_time,
            'end_time': start_time + timedelta(minutes=10),
            'duration': 10*60
        })
        await self.bot.db.muted_members.find_one_and_update(
            {'guild_id': ctx.message.guild.id, 'user_id': member.id},
            {'$set': muted_member.to_primitive()},
            upsert=True
        )

    async def _get_settings(self, ctx: Context):
        settings_cog = ctx.bot.get_cog('Settings')
        return await settings_cog.get_or_create_guild_settings(ctx.message.guild)

    async def _send_messages(self, ctx: Context, member: Member, embeds: Tuple[Embed, Embed]):
        embed, member_embed = embeds
        await ctx.send(embed=embed)
        if member_embed is not None:
            try:
                await member.send(embed=member_embed)
            except Forbidden:
                pass

    async def _build_embed(self, ctx: Context, member: Member,
                           reason: str) -> Tuple[Embed, Embed]:
        embed = Embed(
            title=u'\U0001F507' + ' Usuario Silenciado',
            description='Un usuario ha sido **silenciado** en el servidor.',
            colour=0xFFFF00
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(
            name=u'\U0001F910' + ' Usuario',
            value=get_author_string(member),
            inline=False
        )
        embed.add_field(
            name=u'\U0001F5DE' + ' Razón',
            value=reason,
            inline=False
        )
        # TODO: Add time
        # embed.add_field(
        #     name=u'\U000023F0' + ' Tiempo',
        #     value=f'La duración del silencio es de **{time}** {time_text}.',
        #     inline=False
        # )
        embed.set_footer(
            text=f'Este usuario fue silenciado por {get_author_string(ctx.message.author)}',
            icon_url=ctx.message.author.avatar_url
        )
        if member != ctx.message.author and not member.bot:
            member_embed = Embed(
                title=u'\U0001F910 ' + ctx.message.guild.name,
                description=(
                    f'Has sido silenciado en **{ctx.message.guild.name}** '
                    'y no puedes hablar hasta nuevo aviso.'
                ),
                colour=0xFFFF00
            )
            member_embed.set_thumbnail(url=ctx.message.guild.icon_url)
            member_embed.set_footer(
                text=ctx.message.guild.name,
                icon_url=ctx.message.guild.icon_url
            )
            # TODO: Add time
            # member_embed.add_field(
            #     name=u'\U000023F0' + ' Tiempo',
            #     value=f'La duración del silencio es de **{time}** {time_text}',
            #     inline=False
            # )
            member_embed.add_field(
                name=u'\U0001F5DE' + ' Razón',
                value=reason,
                inline=False
            )
            member_embed.add_field(
                name=u'\U0001F46E' + ' Usuario',
                value=f'Fuiste silenciado por {get_author_string(ctx.message.author)}',
                inline=False
            )
        else:
            member_embed = None
        return embed, member_embed
