from discord.ext import commands
from utils import BaseCommand, get_embed, get_member

NO_REASON = 'No se ha especificado una razón.'


class Exclude(BaseCommand):
    KICK = 0
    BAN = 1
    UNBAN = 2


    @commands.command(name='kick', alias=['echar', 'echa', 'exclude'])
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def exclude(self, ctx, member, *args):
        data = await self.get_member_and_data(
            ctx,
            ctx.message.guild.members,
            member,
            self.KICK,
            *args
        )
        member, kicked_embed, member_kicked_embed, reason = data
        await member.kick(reason=reason)
        await ctx.message.channel.send(embed=kicked_embed)
        try:
            await member.send(embed=member_kicked_embed)
        except:
            pass


    @commands.command(name='ban', aliases=['banear', 'banea'])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member, *args):
        data = await self.get_member_and_data(
            ctx,
            ctx.message.guild.members,
            member,
            self.BAN,
            *args
        )
        member, banned_embed, member_banned_embed, reason = data
        await member.ban(reason=reason)
        await ctx.message.channel.send(embed=banned_embed)
        try:
            await member.send(embed=member_banned_embed)
        except:
            pass


    @commands.command(name='unban', aliases=['desbanear', 'desbanea'])
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member, *args):
        banned_users = await ctx.message.guild.bans()
        banned_users = [u.user for u in banned_users]
        data = await self.get_member_and_data(
            ctx,
            banned_users,
            member,
            self.UNBAN,
            *args
        )
        member, unbanned_embed, member_unbanned_embed, reason = data
        await ctx.message.guild.unban(member, reason=reason)
        await ctx.message.channel.send(embed=unbanned_embed)
        try:
            await member.send(embed=member_unbanned_embed)
        except:
            pass


    async def get_member_and_data(self, ctx, members, member, action, *args):
        member = await get_member(members, member)
        if member is None:
            await ctx.message.channel.send('Debes indicar un miembro válido.')
            return
        reason = " ".join(args) if len(args) > 0 else NO_REASON
        colour = 0xAA0000

        if action == self.KICK:
            action_emoji = u'\U0000274C '
            title = action_emoji+'Usuario Expulsado'
            action_text = 'expulsado'
        elif action == self.BAN:
            action_emoji = u'\U0000274E '
            title = action_emoji+'Usuario Baneado'
            action_text = 'baneado'
        elif action == self.UNBAN:
            action_emoji = u'\U00002705 '
            title = action_emoji+'Usuario Desbaneado'
            action_text = 'desbaneado'
            colour = 0x00AA00

        embed = await get_embed(
            ctx,
            title=title,
            description=f'Un usuario ha sido **{action_text}** del servidor.',
            colour=colour,
            thumbnail=member.avatar_url,
            footer={
                'text': (
                    f'Este usuario fue {action_text} por '
                    f'{ctx.message.author.display_name} ('
                    f'{ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=(
                {
                    'name': u'\U0001F64D '+'Usuario',
                    'value': (
                        f'**{member.display_name}** (*{member.name}#'
                        f'{member.discriminator}*)'
                    ),
                    'inline': False
                },
                {
                    'name': u'\U0001F5DE '+'Razón',
                    'value': reason,
                    'inline': False
                }
            )
        )
        member_embed = await get_embed(
            ctx,
            title=action_emoji+ctx.message.guild.name,
            description=(
                f'Has sido {action_text} de **{ctx.message.guild.name}**.'
            ),
            colour=colour,
            thumbnail=ctx.message.guild.icon_url,
            fields=(
                {
                    'name': u'\U0001F5DE '+'Razón',
                    'value': reason,
                    'inline': False
                },
                {
                    'name': u'\U0001F46E '+'Usuario',
                    'value': (
                        f'Fuiste {action_text} por '
                        f'**{ctx.message.author.display_name}** ('
                        f'*{ctx.message.author.name}#'
                        f'{ctx.message.author.discriminator}*)'
                    ),
                    'inline': False
                }
            )
        )
        return member, embed, member_embed, reason
