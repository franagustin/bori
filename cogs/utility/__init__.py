from discord.ext.commands import Bot

from .colour import Colours
from .info import Information
from .invitation import Invitation
from .ping import Ping


def setup(bot: Bot):
    bot.add_cog(Colours(bot))
    bot.add_cog(Information(bot))
    bot.add_cog(Invitation(bot))
    bot.add_cog(Ping(bot))
