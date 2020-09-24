import dataclasses
import random

from discord.ext.commands import Bot, Cog, command, Context
from discord.ext.commands.errors import CommandError, MissingRequiredArgument

from cogs.converters import SplitValueConverter


@dataclasses.dataclass(eq=False)
class Random(Cog):
    bot: Bot

    @command(name='choose', aliases=['elegir', 'elige', 'decidir', 'decide'])
    async def choose(self, ctx: Context, *, options: SplitValueConverter):
        """Makes a decision for you choosing one of the provided options."""
        await ctx.message.channel.send(f'Elijo: {random.choice(options)}.')

    @choose.error
    async def missing_options(self, ctx: Context, error: CommandError):
        if isinstance(error, MissingRequiredArgument):
            await ctx.message.channel.send('No puedo elegir si no me das opciones.')
            error.handled = True
