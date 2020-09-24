import os
import yaml

from discord.errors import Forbidden
from discord.ext import commands
from discord.ext.commands.errors import CommandError, MissingPermissions
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis

import cogs.checks
from utils.guild_utils import get_prefixes


BOT_TOKEN = os.getenv('BOT_TOKEN')

# TODO: Move this into a different file
class BORICache(Redis):
    # pylint: disable=arguments-differ
    def set(self, key_type, key_name, value):
        return super().set(f'{key_type}-{key_name}', value)

    def set_list(self, key_type, key_name, value):
        value = 'ºsº'.join(value) if value else ''
        return self.set(key_type, key_name, value)

    def get(self, key_type, key_name):
        return super().get(f'{key_type}-{key_name}')

    def get_list(self, key_type, key_name):
        value = self.get(key_type, key_name)
        if value is not None:
            value = value.split('ºsº') if value else []
        return value

    def delete(self, key_type, key_name):
        return super().delete(f'{key_type}-{key_name}')


class BORI(commands.Bot):
    def __init__(self, *args, name='ghost', **kwargs, ):
        super().__init__(*args, **kwargs)
        self.name = name
        self._db_client = None
        self._db = None
        self.config = {}
        # TODO: Use environment variables for this
        self.cache = BORICache(host='localhost', decode_responses=True)

    @property
    def db(self):  # pylint: disable=invalid-name
        if getattr(self, '_db', None) is None:
            self._connect_to_db()
        return self._db

    def _connect_to_db(self):
        mongo_uri = os.getenv('MONGO_URI')
        self._db_client = AsyncIOMotorClient(mongo_uri)
        self._db = self._db_client[self.name]

    def configure(self, filename: str = 'config.yml'):
        with open(filename, 'r') as config_file:
            self.config = yaml.full_load(config_file)
        self._load_all_extensions()
        self._load_all_checks()

    def _load_all_extensions(self):
        for extension in self.config.get('extensions') or []:
            self.load_extension(extension)

    def _load_all_checks(self):
        for check in self.config.get('global_checks') or []:
            if check is not None:
                self.add_check(getattr(cogs.checks, check))


bot = BORI(command_prefix=get_prefixes, case_insensitive=True)


# TODO: Maybe move this to a different file?
@bot.event
async def on_command_error(ctx: commands.Context, error: CommandError):
    def _is_error(error_class: Exception, *errors):
        return any([isinstance(e, error_class) for e in errors])

    if getattr(error, 'handled', False):
        return

    error_messages = ctx.bot.config.get('errors')
    default_error_text = error_messages.get('default', 'ERROR.')
    error_text = error_messages.get(error.__class__.__name__) or default_error_text
    if handled := hasattr(error, 'original') and isinstance(error.original, Forbidden):
        error_text = f'ERROR 403: Forbidden.\n{error_text}'
    elif handled := _is_error(MissingPermissions, error) or (
            hasattr(error, 'errors') and _is_error(MissingPermissions, *error.errors)):
        error_text = f'ERROR: Permissions.\n{error_text}'
    await ctx.message.channel.send(error_text)
    if not handled:
        raise error


@bot.event
async def on_ready():
    print('Ready to go!')


bot.configure('config.yml')
bot.run(BOT_TOKEN)
