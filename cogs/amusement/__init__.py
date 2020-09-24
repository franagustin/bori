from discord.ext.commands import Bot

from .images import Images
from .random import Random
from .talk import Talk


def setup(bot: Bot):
    bot.add_cog(Images(bot))
    bot.add_cog(Random(bot))
    bot.add_cog(Talk(bot))
