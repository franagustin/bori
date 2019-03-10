import discord
import os
import psycopg2
import re
import yaml
from discord.ext.commands import Cog, when_mentioned_or

DB_DATA = yaml.load(open('data/data.yml'))['db_config']
DB_PASSWORD = os.getenv('DB_PASSWORD')
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

def db_connect():
    """Conecta a la base de datos y devuelve la conexión."""
    return psycopg2.connect(
        host=DB_DATA['host'],
        user=DB_DATA['user'],
        password=DB_PASSWORD,
        dbname=DB_DATA['database']
    )

async def get_embed(ctx, title='', description='', colour=0, thumbnail='',
        author=None, footer=None, fields=()):
    """Toma los datos para rellenar el embed y lo devuelve con las 
    propiedades y campos indicados.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
    embed.set_thumbnail(url=thumbnail)
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
