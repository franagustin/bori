from discord.ext import commands
from utils import BaseCommand, get_embed, get_member


class Avatar(BaseCommand):
    @commands.command()
    async def avatar(self, ctx, member=None):
        if member is not None:
            member = await get_member(ctx.message.guild.members, member)
        if member is None:
            member = ctx.message.author
        if member == ctx.message.author:
            footer_text = 'Tú mismo lo pediste'
        else:
            footer_text = (
                f'Avatar pedido por {ctx.message.author.display_name} ('
                f'{ctx.message.author.name}#'
                f'{ctx.message.author.discriminator})'
            )
        avatar_embed = await get_embed(
            ctx,
            title=(
                f'Avatar de {member.display_name} ({member.name}#'
                f'{member.discriminator})'
            ),
            description='',
            colour=0x6C7A89,
            thumbnail='',
            image=member.avatar_url,
            footer={
                'text': footer_text,
                'icon': ctx.message.author.avatar_url
            }
        )
        await ctx.message.channel.send(embed=avatar_embed)
