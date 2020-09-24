import dataclasses
from typing import Union

from discord import Member, Role
from discord.ext.commands import (
    Bot, Cog, command, Context, has_permissions, guild_only, Greedy
)

from cogs.converters import ActionConverter


@dataclasses.dataclass(eq=False)
class Roles(Cog):
    bot: Bot

    @guild_only()
    @has_permissions(manage_roles=True)
    @command(name='role', aliases=['roles', 'rol'])
    async def roles(self, ctx: Context, member: Member, roles: Greedy[Role], *,
                    action: ActionConverter = None):
        """Give, remove or set roles for a member."""
        action = action[0] if action else ''
        role_list = ', '.join([r.name for r in roles])
        if action == 'set':
            await member.edit(roles=roles, reason='Role set command.')
            msg = (
                f'{member.display_name} ahora tiene solamente los siguientes roles: {role_list}'
            )
        else:
            msg = '\n'.join([await self.manage_role(member, role, action) for role in roles])
        await ctx.message.channel.send(msg)

    async def manage_role(self, member: Member, role: Role, action: Union[str, None]) -> str:
        already_has_role = role in member.roles
        action = action if action else 'remove' if already_has_role else 'add'
        if action == 'add':
            if already_has_role:
                msg = f'{member.display_name} ya tiene el rol {role.name}.'
            else:
                await member.add_roles(role, reason='Role add command.')
                msg = f'A {member.display_name} se la ha concedido el rol {role.name}.'
        else:
            if not already_has_role:
                msg = f'{member.display_name} no tiene el rol {role.name}.'
            else:
                await member.remove_roles(role, reason='Role remove command.')
                msg = f'A {member.display_name} se le ha quitado el rol {role.name}.'
        return msg
