from discord.ext import commands
from utils import BaseCommand


class Reverse(BaseCommand):
    @commands.command(name='reverse', aliases=['revés', 'reves', 'reverso'])
    async def reverse(self, ctx, *args):
        to_reverse = " ".join(args) if len(args) > 0 else ctx.message.content
        await ctx.message.channel.send(to_reverse[::-1])
