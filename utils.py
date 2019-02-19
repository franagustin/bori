import discord
import os
import psycopg2
import yaml
from discord.ext.commands import when_mentioned_or

DB_DATA = yaml.load(open('data/data.yml'))['db_config']
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_QUERIES = yaml.load(open('data/db_queries.yml'))


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
        cur.execute(DB_QUERIES['create_prefix_table'])
        cur.execute(
            DB_QUERIES['insert_prefix_returning'],
            (guild, ['g$'])
        )
        conn.commit()
    prefixes = cur.fetchone()[0]
    cur.close()
    conn.close()
    return prefixes

class BaseCommand:
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

def get_embed(ctx, title='', description='', colour=0, thumbnail='',
        fields=()):
    """Toma los datos para rellenar el embed y lo devuelve con las 
    propiedades y campos indicados."""
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
    for field in fields:
        embed.add_field(
            name=field['name'],
            value=field['value'],
            inline=field['inline']
        )
    embed.set_thumbnail(url=thumbnail)
    embed.set_footer(
        text=(
            'Este mensaje es una respuesta a '
            f'{ctx.message.author.display_name} ('
            f'{ctx.message.author.name}#'
            f'{ctx.message.author.discriminator})'
        ),
        icon_url=ctx.message.author.avatar_url
    )
    return embed
