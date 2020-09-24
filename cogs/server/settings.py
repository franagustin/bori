import dataclasses
from random import randint
from typing import List, Tuple

from bori_models.models import GuildSettings
from discord import Embed, Guild, utils as discord_utils
from discord.ext.commands import (
    Bot, check_any, Cog, command, Context, has_permissions, is_owner, RoleConverter
)
from discord.ext.commands.errors import BadArgument
from pymongo.collection import ReturnDocument

from cogs.checks import is_listing
from cogs.converters import ESArgsConverter


VALID_SETTINGS, ALIASES = GuildSettings.valid_settings()  # pylint: disable=no-member
SETTINGS_CONVERTER = ESArgsConverter(valid_args=VALID_SETTINGS, aliases=ALIASES)
SETTINGS_THUMBNAIL = 'https://i.imgur.com/GGRS6wP.png'


@dataclasses.dataclass(eq=False)
class Settings(Cog):
    bot: Bot

    @is_owner()
    @command(name='populate-settings', aliases=['fill-settings', 'create-settings'])
    async def populate_settings(self, ctx: Context):
        """Write settings to database for every guild."""
        for i, guild in enumerate(self.bot.guilds, 1):
            await self.get_or_create_guild_settings(guild)
        # pylint: disable=undefined-loop-variable
        await ctx.message.channel.send(f'Populated settings for all {i} guilds.')

    @check_any(has_permissions(administrator=True), is_listing())
    @command(name='settings', aliases=['ajustes'])
    async def settings(self, ctx: Context, *, args: SETTINGS_CONVERTER = None):
        """List or edit server's settings."""
        action, settings, bad_fields = args if args else ('check', {}, [])
        if action == 'check':
            await self.check_settings(ctx)
            return
        try:
            role = await RoleConverter().convert(ctx, settings.get('muted_role'))
        except (TypeError, BadArgument):
            pass
        else:
            settings['muted_role'] = role.id
        old_settings = (await self.get_or_create_guild_settings(
            ctx.message.guild
        )).to_primitive()
        settings, invalid_fields = self._wrangle_settings(action, old_settings, settings)
        settings = await self._set_guild_settings(ctx.message.guild.id, settings)
        settings_embed = await self._build_embed(settings, ctx.message.guild)
        msg = ''
        msg = f"Ajustes inválidos ignorados: {', '.join(bad_fields)}" if bad_fields else ''
        if invalid_fields:
            msg += f"\nAjustes inválidos para esta acción: {', '.join(invalid_fields)}"
        await ctx.message.channel.send(msg, embed=settings_embed)

    @command(name='check-settings', aliases=['list-settings', 'ver-ajustes', 'listar-ajustes'])
    async def check_settings(self, ctx: Context):
        """List server's settings."""
        settings = await self.get_or_create_guild_settings(ctx.message.guild)
        settings_embed = await self._build_embed(settings, ctx.message.guild)
        await ctx.message.channel.send(embed=settings_embed)

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        await self.get_or_create_guild_settings(guild)

    async def get_or_create_guild_settings(self, guild: Guild) -> GuildSettings:
        result = await self.bot.db.guild_settings.find_one_and_update(
            {'guild_id': guild.id},
            {'$setOnInsert': {'guild_id': guild.id}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return GuildSettings(result)

    async def _set_guild_settings(self, guild_id: int, new_settings: dict) -> GuildSettings:
        if new_settings:
            set_dict = {'$set': new_settings}
        else:
            set_dict = {'$setOnInsert': {'guild_id': guild_id}}
        settings = await self.bot.db.guild_settings.find_one_and_update(
            {'guild_id': guild_id},
            set_dict,
            return_document=ReturnDocument.AFTER
        )
        for key, value in settings.items():
            if key == '_id':
                continue
            if isinstance(value, list):
                self.bot.cache.set_list(key, guild_id, value)
            else:
                self.bot.cache.set(key, guild_id, value)
        return GuildSettings(settings)

    async def _build_embed(self, settings: GuildSettings, guild: Guild) -> Embed:
        embed = Embed(
            title=u'\U00002699' + ' Settings',
            description=f'Configuraciones para el servidor: {guild.name}',
            colour=randint(0, 0xFFFFFF)
        )
        muted_role = discord_utils.get(guild.roles, id=settings.muted_role)
        embed.add_field(
            name=u'\U0001F507' + ' Muted Role',
            value=getattr(muted_role, 'mention', 'Ninguno'),
            inline=False
        )
        if settings.disabled_cogs:
            disabled_cogs = self._parse_list(settings.disabled_cogs, '*')
        else:
            disabled_cogs = 'Ninguno'
        embed.add_field(
            name=u'\U0000274C' + ' Cogs deshabilitados',
            value=disabled_cogs
        )
        if settings.disabled_commands:
            disabled_commands = self._parse_list(settings.disabled_commands, '*')
        else:
            disabled_commands = 'Ninguno'
        embed.add_field(
            name=u'\U0001F6AB' + ' Comandos deshabilitados',
            value=disabled_commands
        )
        if settings.prefixes:
            prefixes = self._parse_list(settings.prefixes)
        else:
            prefixes = '$'
        embed.add_field(
            name=u'\U0001D11E' + ' Prefijos (*uno por línea*)',
            value=prefixes,
            inline=False
        )
        embed.set_thumbnail(url=SETTINGS_THUMBNAIL)
        embed.set_footer(text=guild.name, icon_url=guild.icon_url)
        return embed

    def _parse_list(self, values: list, item: str = '') -> str:  # pylint: disable=no-self-use
        return '\n'.join([f'{item} {v}' for v in values])

    def _wrangle_settings(self, action: str, old_settings: dict,
                          new_settings: dict) -> Tuple[dict, List[str]]:
        # pylint: disable=no-self-use
        invalid_fields = []
        for field, value in new_settings.items():
            is_multiple = isinstance(value, list)
            if not is_multiple and action in ('add', 'remove'):
                invalid_fields.append(field)
            elif is_multiple and action == 'add':
                new_settings[field].extend([v for v in old_settings[field] if v not in value])
            elif is_multiple and action == 'remove':
                new_settings[field] = [v for v in old_settings[field] if v not in value]
        for field in invalid_fields:
            del new_settings[field]
        return new_settings, invalid_fields
