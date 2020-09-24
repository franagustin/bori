import dataclasses

from discord.ext.commands import Bot, Cog, command, Context


@dataclasses.dataclass(eq=False)
class Talk(Cog):
    bot: Bot

    @command(name='say', aliases=['repeat', 'decir', 'di', 'repetir'])
    async def say(self, ctx: Context, *, text):
        """Send a message with provided content, deleting the original."""
        await ctx.message.delete()
        await ctx.message.channel.send(text)

    @command(name='reverse', aliases=['yas', 'revés', 'reves', 'reverso', 'revertir'])
    async def reverse(self, ctx: Context, *, text):
        """Repeat a message backwards."""
        await ctx.message.channel.send(text[::-1])
