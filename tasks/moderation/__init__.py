from .silence import UnmuteTaskLoop


def setup(bot):
    bot.custom_tasks.append(UnmuteTaskLoop(bot))
