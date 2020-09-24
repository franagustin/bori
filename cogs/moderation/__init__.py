from discord.ext.commands import Bot

from .exclude import Exclude
from .nickname import Nickname
from .role import Roles
from .silence import Silence


def setup(bot: Bot):
    bot.add_cog(Exclude(bot))
    bot.add_cog(Nickname(bot))
    bot.add_cog(Roles(bot))
    bot.add_cog(Silence(bot))
