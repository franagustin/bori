from .info import BotInfo
from .invitation import Invitation
from .ping import Ping
from .prefix import Prefix
from .colour import Colour


def setup(bot):
    bot.add_cog(BotInfo(bot))
    bot.add_cog(Invitation(bot))
    bot.add_cog(Ping(bot))
    bot.add_cog(Prefix(bot))
    bot.add_cog(Colour(bot))
