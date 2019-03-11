from discord.ext import commands
from utils import BaseCommand


class Nickname(BaseCommand):
    @commands.command(name='nick', aliases=['apodo', 'nickname'])
    @commands.guild_only()
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
            f'El nuevo nick para *{member.name}#{member.discriminator}* es '
            f'**{new_nick}**'
        )
