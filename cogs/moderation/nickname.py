import dataclasses

from discord import Member
from discord.ext.commands import (
    Bot, check_any, Cog, command, Context, guild_only, has_permissions
)

from cogs.checks import can_change_nickname
from utils.guild_utils import get_user_string


@dataclasses.dataclass(eq=False)
class Nickname(Cog):
    bot: Bot

    @guild_only()
    @check_any(has_permissions(manage_nicknames=True), can_change_nickname())
    @command(name='nick', aliases=['nickname', 'apodo', 'mote'])
    async def nickname(self, ctx: Context, member: Member, *, nickname: str):
        """Change a user's nickname on this server, may be yourself."""
        await member.edit(nick=nickname, reason='Nickname change command.')
        await ctx.message.channel.send(
            f'El nuevo nick para *{get_user_string(member)}* es **{nickname}**.'
        )
