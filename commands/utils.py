import discord


class BaseCommand:
    def __init__(self, bot):
        self.bot = bot

def get_embed(title='', description='', colour=0, thumbnail='', fields=()):
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
    #pong_embed.set_footer(
    #text="Este mensaje es una respuesta a {} ({}#{})"
    #icon_url=avatar_autor
    #)
    return embed
