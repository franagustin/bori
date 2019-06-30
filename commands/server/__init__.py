from .persistent_role import PersistentRole
from .rainbow_role import RainbowRole


def setup(bot):
    bot.add_cog(PersistentRole(bot))
    bot.add_cog(RainbowRole(bot))
