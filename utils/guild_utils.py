import os
from typing import Union, Sequence, Tuple

import discord
from discord.ext.commands import Bot, when_mentioned_or


DEFAULT_PREFIX = os.getenv('BOT_DEFAULT_PREFIX', '$')
SEARCH = Union[int, str, Tuple[str]]


def get_user_string(user: discord.User) -> str:
    return f'{user.name}#{user.discriminator}'


def get_author_string(author: discord.User) -> str:
    return f'{author.display_name} ({get_user_string(author)})'


async def get_prefixes(bot: Bot, message: discord.Message):
    guild_prefixes = await get_guild_prefixes(bot, message.guild.id)
    return when_mentioned_or(*guild_prefixes)(bot, message)


async def get_guild_prefixes(bot: Bot, guild_id: int):
    settings = bot.cache.get('prefixes', guild_id)
    if settings is None:
        settings = await bot.db.guild_settings.find_one({'guild_id': guild_id})
        settings = settings or {}
        prefixes = settings.get('prefixes') or [DEFAULT_PREFIX]
        bot.cache.set('prefix', guild_id, 'ºsº'.join(prefixes))
    else:
        prefixes = settings.split('ºsº')
    return prefixes


def role_exists(role_list: Sequence[discord.Role], search_value: str, search_key: str = 'id'):
    return discord.utils.get(role_list, **{search_key: search_value}) is not None


def get_role(roles: Sequence[discord.Role], role_search: SEARCH) -> discord.Role:
    """DEPRECATED. Use discord.ext.commands.RoleConverter's convert method instead."""
    if role_search is None:
        return None
    if isinstance(role_search, str):
        role_search = (role_search, )
    try:
        role = discord.utils.get(roles, id=int(role_search[0]))
    except ValueError:
        role = discord.utils.get(roles, mention=role_search[0])
    if role is None:
        role = discord.utils.get(roles, name=role_search[0])
    if role is None:
        role_search = " ".join(role_search)
        role = discord.utils.get(roles, name=role_search)
    if role is None:
        for guild_role in roles:
            if guild_role.name.lower().startswith(role_search.lower()):
                role = guild_role
    return role
