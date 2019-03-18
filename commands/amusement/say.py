from discord.ext import commands
from utils import BaseCommand


class Say(BaseCommand):
    @commands.command(name='say', aliases=['decir', 'di'])
    async def say(self, ctx, *args):
        await ctx.message.delete()
        text = " ".join(args) if len(args) > 0 else u'\u200C'
        await ctx.message.channel.send(text)
