import dataclasses
from random import randint
from typing import Optional, Tuple

from discord import Colour, Embed, Member
from discord.ext.commands import Bot, Cog, command, Context
from http3 import AsyncClient

from utils.guild_utils import get_author_string


COLOUR_API_URL = 'https://www.thecolorapi.com/id/?hex={}'
COLOUR_IMAGE_URL = (
    'http://laruedacuadrada.com/ghosties/?red={}&green={}&blue={}&width=80&height=80'
)


@dataclasses.dataclass(eq=False)
class Colours(Cog):
    bot: Bot
    requests: AsyncClient = AsyncClient()

    @command(name='colour', aliases=['color'])
    async def colour(self, ctx: Context, colour: Optional[Colour]):
        """Display information for a given or random colour."""
        colour = colour or Colour(randint(0, 0xFFFFFF))
        colour_data = await self._get_colour_data(colour)
        colour_embed = await self._build_embed(colour_data, ctx.message.author)
        await ctx.message.channel.send(embed=colour_embed)

    async def _get_colour_data(self, colour: Colour) -> dict:
        colour_data = await self.requests.get(COLOUR_API_URL.format(str(colour)[1:]))
        colour_data = colour_data.json()
        colour_data = {
            'value': int(colour_data['hex']['clean'], 16),
            'value_string': colour_data['hex']['value'],
            'image': COLOUR_IMAGE_URL.format(
                colour_data['rgb']['r'],
                colour_data['rgb']['g'],
                colour_data['rgb']['b']
            ),
            'fields': await self._get_colour_fields(colour_data)
        }
        return colour_data

    async def _get_colour_fields(self, colour_data: dict) -> Tuple[dict]: 
        # pylint: disable=no-self-use
        name_match = '' if colour_data['name']['exact_match_name'] else ' *(Más cercano)*'
        return (
            {
                'name': u'\U0001F5BC' + ' Nombre',
                'value': f"{colour_data['name']['value']}{name_match}",
                'inline': False
            },
            {
                'name': u'\U0001F58C' + ' Valor Hex',
                'value': colour_data['hex']['value'],
                'inline': True
            },
            {
                'name': u'\U0000270F' + ' Valor RGB',
                'value': colour_data['rgb']['value'],
                'inline': True
            },
            {
                'name': u'\U0000270F' + ' Valor HSL',
                'value': colour_data['hsl']['value'],
                'inline': True
            },
            {
                'name': u'\U0001F58C' + ' Valor HSV',
                'value': colour_data['hsv']['value'],
                'inline': True
            },
            {
                'name': u'\U0001F58C' + ' Valor CMYK',
                'value': colour_data['cmyk']['value'],
                'inline': True
            },
            {
                'name': u'\U0000270F' + ' Valor XYZ',
                'value': colour_data['XYZ']['value'],
                'inline': True
            }
        )

    async def _build_embed(self, colour_data: dict, author: Member) -> Embed:
        embed = Embed(
            title=u'\U0001F3A8'+' Color Aleatorio',
            description=f"Este es el color {colour_data['value_string']}.",
            colour=colour_data['value']
        )
        embed.set_thumbnail(url=colour_data['image'])
        embed.set_footer(
            text=f'Color requerido por {get_author_string(author)}',
            icon_url=colour_data['image']
        )
        for field in colour_data['fields']:
            embed.add_field(**field)
        return embed
