import yaml
from discord.ext import commands
from utils import BaseCommand, get_embed

DATA = yaml.load(open('data/data.yml'))


class BotInfo(BaseCommand):
    @commands.command(name='info', aliases=[
        'información', 'informacion', 'information'
    ])
    async def information(self, ctx):
        info_embed = await get_embed(
            ctx,
            title=u'\U00002139 '+DATA['info title'],
            description=DATA['info description'],
            colour=0x2464CC,
            thumbnail=self.bot.user.avatar_url,
            author={
                'name': 'Franco Peluix',
                'url': 'https://github.com/francokuchiki/bori/',
                'icon': 'https://avatars1.githubusercontent.com/u/39889930'
            },
            footer={
                'text': (
                    'Información solicitada por '
                    f'{ctx.message.author.display_name} ('
                    f'{ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=(
                {
                    'name': 'Versión',
                    'value': DATA['version'],
                    'inline': True
                },
                {
                    'name': 'Versión BORI (base)',
                    'value': DATA['base version'],
                    'inline': True
                },
                {
                    'name': 'Código fuente',
                    'value': DATA['source code url'],
                    'inline': False
                }
            )
        )
        await ctx.message.channel.send(embed=info_embed)
