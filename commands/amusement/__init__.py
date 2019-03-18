from .avatar import Avatar
from .choose import Choose
from .reverse import Reverse
from .say import Say


def setup(bot):
    bot.add_cog(Avatar(bot))
    bot.add_cog(Choose(bot))
    bot.add_cog(Reverse(bot))
    bot.add_cog(Say(bot))
