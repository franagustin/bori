from discord.ext.commands import Bot

from .settings import Settings


def setup(bot: Bot):
    bot.add_cog(Settings(bot))
