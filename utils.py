import discord
import os
import psycopg2
import re
import tasks
import yaml
from discord.ext.commands import Cog, when_mentioned_or

DB_DATA = yaml.load(open('data/data.yml'))['db_config']
DB_PASSWORD = os.getenv('DB_PASSWORD_COPY_X')
DB_QUERIES = yaml.load(open('data/db_queries.yml'))

TIME_PATTERN = re.compile(r'^[0-9]+s?m?h?d?w?a?y?c?$')
NUMBER_PATTERN = re.compile(r'^[0-9]+$')

async def get_guild_prefixes(bot, message):
    """Función pasada al crear el commands.Bot. Lee desde la bd los prefijos
    disponibles para el servidor.
    El bot reaccionará si el mensaje trae uno de ellos o si es mencionado.
    """
    guild_prefixes = await get_prefixes(message.guild.id)
    return when_mentioned_or(*guild_prefixes)(bot, message)

async def get_prefixes(guild_id):
    """Conecta con la bd y devuelve una lista con todos los prefijos para
    el servidor."""
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute(DB_QUERIES['select_prefixes'], (guild_id,))
        prefixes = cur.fetchone()[0]
    except:
        conn.rollback()
        cur.execute(DB_QUERIES['create_prefix_table'])
        cur.execute(
            DB_QUERIES['insert_prefix_returning'],
            (guild_id, ['g$'])
        )
        conn.commit()
        prefixes = cur.fetchone()[0]
    cur.close()
    conn.close()
    return prefixes

class BaseCommand(Cog):
    """Clase base para evitar definir __init__ en cada grupo de comandos."""
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_listener(self.on_member_join)

    async def on_member_join(self, member):
        on_member_join_funcs = [
            getattr(self, a) for a in dir(self) if
            a.startswith('_on_member_join_')
        ]
        on_member_join_funcs = [
            f for f in on_member_join_funcs if callable(f)
        ]
        for func in on_member_join_funcs:
            await func(member)


class BaseTask:
    def __init__(self, bot):
        self.bot = bot
        tasks = [getattr(self, a) for a in dir(self) if not a.startswith('_')]
        tasks = [t for t in tasks if callable(t)]
        for task in tasks:
            self.bot.loop.create_task(task())


def db_connect():
    """Conecta a la base de datos y devuelve la conexión."""
    return psycopg2.connect(
        host=DB_DATA['host'],
        user=DB_DATA['user'],
        password=DB_PASSWORD,
        dbname=DB_DATA['database']
    )

async def get_embed(ctx, title='', description='', colour=0, thumbnail='',
        author=None, footer=None, image=None, fields=()):
    """Toma los datos para rellenar el embed y lo devuelve con las 
    propiedades y campos indicados.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
    embed.set_thumbnail(url=thumbnail)
    if image is not None:
        embed.set_image(url=image)
    if author is not None:
        embed.set_author(
            name=author['name'],
            url=author['url'],
            icon_url=author['icon']
        )
    if footer is not None:
        embed.set_footer(text=footer['text'], icon_url=footer['icon'])
    for field in fields:
        embed.add_field(
            name=field['name'],
            value=field['value'],
            inline=field['inline']
        )
    return embed

async def get_member(members, member_search):
    try:
        member = discord.utils.get(members, id=int(member_search))
    except:
        member = discord.utils.get(members, mention=member_search)
    if member is None:
        member = discord.utils.get(members, name=member_search)
    return member

async def get_role(roles, role_search):
    try:
        role = discord.utils.get(roles, id=int(role_search[0]))
    except:
        role = discord.utils.get(roles, mention=role_search[0])
    if role is None:
        role = discord.utils.get(roles, name=role_search[0])
    if role is None:
        role_search = " ".join(role_search)
        for guild_role in roles:
            if guild_role.name.lower().startswith(role_search.lower()):
                role = guild_role
    return role

async def get_muted_role(roles):
    muted_role_names = ('Silenciado', 'Muted', 'callate', 'CALLATE BOLUDO')
    for role_name in muted_role_names:
        muted_role = await get_role(roles, (role_name,))
        if muted_role is not None:
            break
    return muted_role

def get_custom_tasks(bot):
    tasks_modules = [
        getattr(tasks, a) for a in dir(tasks) if not a.startswith('_')
    ]
    tasks_classes = []
    print(dir(tasks))
    for t in tasks_modules:
        tasks_submodules = [
            getattr(t, a) for a in dir(t) if not a.startswith('_')
        ]
        print(dir(t))
        for t in tasks_submodules:
            tasks_loops = [
                getattr(t, a) for a in dir(t) if not a.startswith('_') and \
                a.endswith('TaskLoop')
            ]
            tasks_loops = [t for t in tasks_loops if isinstance(t, type)]
            tasks_classes += tasks_loops
    #raise Exception(tasks_classes)
    return [t(bot) for t in tasks_classes]
