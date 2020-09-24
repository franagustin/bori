import dataclasses
from typing import Tuple

from discord import Embed, Member, User
from discord.errors import Forbidden
from discord.ext.commands import Bot, Cog, command, Context, guild_only, has_permissions


from utils.guild_utils import get_author_string


NO_REASON = 'No se ha especificado una razón.'


@dataclasses.dataclass(eq=False)
class Exclude(Cog):
    bot: Bot

    KICK = 0  # pylint: disable=invalid-name
    BAN = 1  # pylint: disable=invalid-name
    UNBAN = 2  # pylint: disable=invalid-name

    @guild_only()
    @has_permissions(kick_members=True)
    @command(name='kick', aliases=['exclude', 'echar', 'echa', 'kickear', 'kickea'])
    async def kick(self, ctx: Context, member: Member, *, reason: str = NO_REASON):
        """Kick a member from this server."""
        embeds = await self._build_embed(member, reason, self.KICK, ctx)
        await member.kick(reason=reason)
        await self._send_messages(ctx, member, embeds)

    @guild_only()
    @has_permissions(ban_members=True)
    @command(name='ban', aliases=['prohibir', 'prohibe', 'banear', 'banea'])
    async def ban(self, ctx: Context, member: Member, *, reason: str = NO_REASON):
        """Ban a member from this server."""
        embeds = await self._build_embed(member, reason, self.BAN, ctx)
        await member.ban(reason=reason)
        await self._send_messages(ctx, member, embeds)

    @guild_only()
    @has_permissions(ban_members=True)
    @command(name='unban', aliases=['desbanear', 'desbanea'])
    async def unban(self, ctx: Context, user: User, *, reason: str = NO_REASON):
        """Unban a member from this server."""
        embeds = await self._build_embed(user, reason, self.UNBAN, ctx)
        await ctx.message.guild.unban(user, reason=reason)
        await self._send_messages(ctx, user, embeds)

    async def _send_messages(self, ctx: Context, member: Member, embeds: Tuple[Embed, Embed]):
        embed, member_embed = embeds
        await ctx.send(embed=embed)
        if member_embed is not None:
            try:
                await member.send(embed=member_embed)
            except Forbidden:
                pass

    async def _build_embed(self, member: Member, reason: str, action: int,
                           ctx: Context) -> Embed:
        colour = 0xAA0000
        if action == self.KICK:
            action_emoji = u'\U0000274C '
            title = action_emoji + ' Usuario Expulsado'
            action_text = 'expulsado'
        elif action == self.BAN:
            action_emoji = u'\U0000274E '
            title = action_emoji + ' Usuario Baneado'
            action_text = 'baneado'
        elif action == self.UNBAN:
            action_emoji = u'\U00002705 '
            title = action_emoji + ' Usuario Desbaneado'
            action_text = 'desbaneado'
            colour = 0x00AA00
        author_string = get_author_string(ctx.message.author)
        embed = Embed(
            title=title,
            description=f'Un usuario ha sido **{action_text}** del servidor.',
            colour=colour
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(
            text=f'Este usuario fue {action_text} por {author_string}',
            icon_url=ctx.message.author.avatar_url
        )
        embed.add_field(
            name=u'\U0001F64D' + ' Usuario',
            value=get_author_string(member),
            inline=False
        )
        embed.add_field(
            name=u'\U0001F5DE' + ' Razón',
            value=reason,
            inline=False
        )

        if member != ctx.message.author and not member.bot:
            member_embed = Embed(
                title=action_emoji + ctx.message.guild.name,
                description=f'Has sido {action_text} de **{ctx.message.guild.name}**',
                colour=colour
            )
            member_embed.set_thumbnail(url=ctx.message.guild.icon_url)
            member_embed.add_field(
                name=u'\U0001F5DE' + ' Razón',
                value=reason,
                inline=False
            )
            member_embed.add_field(
                name=u'\U0001F46E' + ' Usuario',
                value=f'Fuiste {action_text} por {author_string}',
                inline=False
            )
        else:
            member_embed = None
        return embed, member_embed
