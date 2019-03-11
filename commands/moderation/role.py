from discord.ext import commands
from utils import BaseCommand, get_member, get_role


class Role(BaseCommand):
    @commands.command(name='rol', aliases=['roles', 'role'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, *args):
        if len(args) < 2:
            await ctx.message.channel.send('Debes indicar miembro y rol.')
            return
        member_search = args[1]
        role_search = args[2:]
        if args[0] in TEXTS['add']:
            action = 'add'
        elif args[0] in TEXTS['rm']:
            action = 'rm'
        elif args[0] in TEXTS['set']:
            action = 'set'
        else:
            action = None
            member_search = args[0]
            role_search = args[1:]
        member = await get_member(ctx.message.guild.members, member_search)
        if member is None:
            await ctx.message.channel.send('Debes indicar un miembro válido.')
            return
        role = await get_role(ctx.message.guild.roles, role_search)
        if role is None:
            await ctx.message.channel.send('Debes indicar un rol válido.')
            return
        if action is None and role in member.roles:
            action = 'rm'
        elif action is None:
            action = 'add'
        if action == 'add':
            if role in member.roles:
                await ctx.message.channel.send(
                    f'{member.display_name} ya tiene el rol {role.name}.'
                )
                return
            await member.add_roles(role, reason='Role add command.')
            await ctx.message.channel.send(
                f'A {member.display_name} se la ha concedido el rol '
                f'{role.name}.'
            )
        elif action == 'rm':
            if role not in member.roles:
                await ctx.message.channel.send(
                    f'{member.display_name} no tiene el rol {role.name}.'
                )
                return
            await member.remove_roles(role, reason='Role remove command.')
            await ctx.message.channel.send(
                f'A {member.display_name} se le ha quitado el rol '
                f'{role.name}.'
            )
        else:
            await member.edit(roles=[role], reason='Role set command.')
            await ctx.message.channel.send(
                f'Se ha establecido {role.name} como el único rol de '
                f'{member.display_name}.'
            )
