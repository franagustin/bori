import discord
import importlib
import os
import yaml
from discord.ext import commands
from utils import BaseTask, get_custom_tasks, get_guild_prefixes


data = yaml.load(open('data/data.yml'))

TOKEN = os.getenv('GHOST_TOKEN')

bot = commands.Bot(
    command_prefix=get_guild_prefixes,
    case_insensitive=True
)

if __name__ == '__main__':
    for group in data['command_groups']:
        bot.load_extension(group)

    bot.custom_tasks = []
    for task in data['task_groups']:
        importlib.import_module(task).setup(bot)

    bot.run(TOKEN)
