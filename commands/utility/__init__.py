from .info import BotInfo
from .ping import Ping
from .prefix import Prefix


def setup(bot):
    bot.add_cog(BotInfo(bot))
    bot.add_cog(Ping(bot))
    bot.add_cog(Prefix(bot))
