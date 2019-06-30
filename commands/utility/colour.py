import requests
from discord.ext import commands
from random import randint
from utils import BaseCommand, get_embed


COLOUR_API_URL = 'https://www.thecolorapi.com/id/'
COLOUR_IMAGE_URL = 'https://color.dyno.gg/color/{}/80x80.png'


class Colour(BaseCommand):
    @commands.command(name='colour', aliases=['color'])
    async def colour(self, ctx, *colour_data):
        if colour_data:
            colour = " ".join(colour_data)
            colour_rgb = await self._parse_colour(colour)
            if colour_rgb is None:
                await ctx.message.channel.send(
                    f'Formato de color "{colour}" inválido.'
                )
                return
        else:
            colour_rgb = await self._get_random_colour()

        colour_data = await self._get_colour_data(colour_rgb)

        colour_embed = await get_embed(
            ctx,
            title=u'\U0001F3A8'+' Color Aleatorio',
            description=f"Este es el color {colour_data['value_string']}.",
            colour=colour_data['value'],
            thumbnail=colour_data['image'],
            footer={
                'text': (
                    f'Color requerido por {ctx.message.author.display_name} '
                    f'({ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=colour_data['fields']
        )
        await ctx.message.channel.send(embed=colour_embed)

    async def _parse_colour(self, colour):
        if colour.startswith('rgb(') and colour.endswith(')'):
            raw_colour = colour.replace('rgb(', '').replace(')', '')
            raw_colour = raw_colour.replace(' ', '')
            colour_rgb = raw_colour.split(',')
            for i in range(len(colour_rgb)):
                colour_rgb[i] = int(colour_rgb[i])
            if max(*colour_rgb) > 255 or min(*colour_rgb) < 0:
                colour_rgb = None
        else:
            if colour.startswith('#') or colour.startswith('x'):
                i = 1
            elif colour.startswith('0x'):
                i = 2
            else:
                i = 0
            if (i == 0 and len(colour) < 6) or (i == 1 and len(colour) < 7) \
                    or (i == 2 and len(colour) < 8):
                colour_rgb = None
            else:
                colour_rgb = [colour[i:i+2], colour[i+2:i+4], colour[i+4:i+6]]
                for i in range(len(colour_rgb)):
                    colour_rgb[i] = int(colour_rgb[i], 16)
        if colour_rgb is not None and len(colour_rgb) < 3:
            colour_rgb = None
        return colour_rgb

    async def _get_random_colour(self):
        colour_rgb = []
        for i in range(3):
            colour_rgb.append(randint(0, 255))
        return colour_rgb

    async def _get_colour_data(self, colour_rgb):
        rgb_string = f'rgb({colour_rgb[0]},{colour_rgb[1]},{colour_rgb[2]})'
        colour = requests.get(COLOUR_API_URL, params={'rgb': rgb_string})
        colour = colour.json()
        name_match = '' if colour['name']['exact_match_name'] \
                     else '*(Más cercano)*'
        colour_data = {
            'value': int(colour['hex']['clean'], 16),
            'value_string': colour['hex']['value'],
            'image': COLOUR_IMAGE_URL.format(colour['hex']['clean']),
            'fields': (
                {
                    'name': u'\U0001F5BC' + ' Nombre',
                    'value': f"{colour['name']['value']} {name_match}",
                    'inline': False
                },
                {
                    'name': u'\U0001F58C' + ' Valor Hex',
                    'value': colour['hex']['value'],
                    'inline': True
                },
                {
                    'name': u'\U0000270F' + ' Valor RGB',
                    'value': colour['rgb']['value'],
                    'inline': True
                },
                {
                    'name': u'\U0000270F' + ' Valor HSL',
                    'value': colour['hsl']['value'],
                    'inline': True
                },
                {
                    'name': u'\U0001F58C' + ' Valor HSV',
                    'value': colour['hsv']['value'],
                    'inline': True
                },
                {
                    'name': u'\U0001F58C' + ' Valor CMYK',
                    'value': colour['cmyk']['value'],
                    'inline': True
                },
                {
                    'name': u'\U0000270F' + ' Valor XYZ',
                    'value': colour['XYZ']['value'],
                    'inline': True
                }
            )
        }
        return colour_data
