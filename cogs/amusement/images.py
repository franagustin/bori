import dataclasses

from discord import Embed, Member
from discord.ext.commands import Bot, Cog, command, Context

from utils.guild_utils import get_author_string


@dataclasses.dataclass(eq=False)
class Images(Cog):
    bot: Bot

    @command(name='avatar')
    async def avatar(self, ctx: Context, member: Member = None):
        """Shows provided member's avatar or yours by default."""
        member = member or ctx.message.author
        avatar_embed = await self._build_embed(member, ctx.message.author)
        await ctx.message.channel.send(embed=avatar_embed)

    async def _build_embed(self, member: Member, author: Member) -> Embed:
        if member == author:
            footer_text = 'Tú mismo lo pediste'
        else:
            footer_text = f'Avatar pedido por {get_author_string(author)}'
        embed = Embed(title=f'Avatar de {get_author_string(member)}', colour=0x6C7A89)
        embed.set_image(url=member.avatar_url)
        embed.set_footer(text=footer_text, icon_url=author.avatar_url)
        return embed
