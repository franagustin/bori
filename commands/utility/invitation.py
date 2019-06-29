from discord.ext import commands
from utils import BaseCommand, get_embed


class Invitation(BaseCommand):
    @commands.command(name='invitation', aliases=[
        'invite', 'invitacion', 'invitación', 'invitar'
    ])
    async def invitation(self, ctx, server=None):
        if server is not None:
            await ctx.message.channel.send('Not Implemented Yet.')
            return

        bot_invitation_url = (
            'https://discordapp.com/api/oauth2/authorize?'
            f'client_id={self.bot.user.id}&'
            'permissions=1543825495&scope=bot'
        )
        author_text = (
            f'{ctx.message.author.display_name} ('
            f'{ctx.message.author.name}#'
            f'{ctx.message.author.discriminator})'
        )

        invite_embed = await get_embed(
            ctx,
            title=u'\U0001F4E9'+' Invitación',
            description=f'[Invítame a tu server]({bot_invitation_url}).',
            colour=0xFA3E7D,
            thumbnail=(
                'https://cdn0.iconfinder.com/data/icons/'
                'party-and-celebrations-8/128/242-512.png'
            ),
            footer={
                'text': f'Invitación solicitada por {author_text}.',
                'icon': ctx.message.author.avatar_url
            }
        )
        await ctx.message.channel.send(embed=invite_embed)
