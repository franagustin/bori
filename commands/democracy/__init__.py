from .polls import Polls


def setup(bot):
    bot.add_cog(Polls(bot))