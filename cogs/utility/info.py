import dataclasses

from discord import Embed, Member
from discord.ext.commands import Bot, Cog, command, Context

from utils.guild_utils import get_author_string


@dataclasses.dataclass(eq=False)
class Information(Cog):
    bot: Bot

    @command(name='info', aliases=['information', 'informacion', 'información'])
    async def information(self, ctx: Context):
        """Display bot's information."""
        info_embed = await self._build_embed(ctx.message.author)
        await ctx.message.channel.send(embed=info_embed)

    async def _build_embed(self, message_author: Member) -> Embed:
        bot_information = self.bot.config.get('info')
        embed = Embed(
            title=u'\U00002139 ' + bot_information.get('title'),
            description=bot_information.get('description'),
            colour=0x2464CC
        )
        bot_author = bot_information.get('author', {})
        embed.set_author(
            name=bot_author.get('name'),
            url=bot_author.get('url'),
            icon_url=bot_author.get('icon_url')
        )
        embed.set_footer(
            text=f'Información solicitada por {get_author_string(message_author)}',
            icon_url=message_author.avatar_url
        )
        embed.add_field(name='Versión', value=bot_information.get('version'))
        embed.add_field(name='Código fuente', value=bot_information.get('source_url'))
        return embed
