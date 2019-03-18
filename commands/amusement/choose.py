import random
from discord.ext import commands
from utils import BaseCommand


class Choose(BaseCommand):
    @commands.command(name='choose', aliases=[
        'chooser', 'elegir', 'elige', 'decidir', 'decide'
    ])
    async def choose(self, ctx, *args):
        msg = " ".join(args) if len(args) > 0 else ""
        if '|' in msg:
            splitter = '|'
        elif ';' in msg:
            splitter = ';'
        else:
            splitter = ','
        options = msg.split(splitter)
        if len(options) < 2:
            await ctx.message.channel.send(
                'Debes darme al menos dos opciones.'
            )
            return
        chosen = random.choice(options)
        await ctx.message.channel.send(f'Elijo: {chosen.strip()}.')
