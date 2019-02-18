import discord
import os
import yaml
from discord.ext import commands

def get_prefixes(bot, message):
    return ''

data = yaml.load(open('data.yml'))

TOKEN = os.getenv('GHOST_TOKEN')

bot = commands.Bot(
    command_prefix=get_prefixes,
    case_insensitive=True
)

if __name__ == '__main__':
    for group in data['command_groups']:
        bot.load_extension(group)
    bot.run(TOKEN)
