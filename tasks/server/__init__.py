from .rainbow_role import RainbowRoleTaskLoop


def setup(bot):
    bot.custom_tasks.append(RainbowRoleTaskLoop(bot))
