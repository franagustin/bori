import discord
import yaml
from discord.ext import commands
from utils import BaseCommand, get_member, get_role

TEXTS = yaml.load(open('data/texts/moderation.yml'))


class Moderation(BaseCommand):
    @commands.command(name='nick', aliases=['apodo', 'nickname'])
    async def nickname(self, ctx, member, *args):
        manage_nicks = ctx.message.author.guild_permissions.manage_nicknames
        change_nick = ctx.message.author.guild_permissions.change_nickname
        member = await get_member(ctx.message.guild.members, member)
        if member is None:
            await ctx.message.channel.send('Debes indicar un miembro del servidor.')
            return
        elif (member != ctx.message.author and not manage_nicks) or \
                (member == ctx.message.author and not change_nick):
            await ctx.message.channel.send('No tienes los permisos suficientes.')
            return
        new_nick = " ".join(args) if len(args) >= 1 else None
        await member.edit(
            nick=new_nick,
            reason='Nickname change command.'
        )
        new_nick = member.name if new_nick is None else new_nick
        await ctx.message.channel.send(
            f'El nuevo nick para {member.name}#{member.discriminator} es '
            f'{new_nick}'
        )
    
    
    @commands.command(name='rol', aliases=['roles', 'role'])
    async def role(self, ctx, *args):
        if not ctx.message.author.guild_permissions.manage_roles:
            await ctx.message.channel.send('No tienes los permisos necesarios.')
            return
        elif len(args) < 2:
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


def setup(bot):
    bot.add_cog(Moderation(bot))
