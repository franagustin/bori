import asyncio
import yaml
from datetime import datetime, timedelta
from discord.ext import commands
from random import randint
from utils import BaseCommand, db_connect, get_embed, get_role


DB_QUERIES = yaml.load(open('data/db_queries.yml'))
TEXTS = yaml.load(open('data/texts/server.yml'))
RAINBOW_COLOURS = [
    0xEE82EE,
    0x4B0082,
    0x0000FF,
    0x008000,
    0xFFFF00,
    0xFFA500,
    0xFF0000
]


class RainbowRole(BaseCommand):
    @commands.command(name='rainbow-role', aliases=[
        'rainbow-roles', 'rainbow_role', 'rainbow_roles', 'rrole', 'rroles',
        'r-role', 'r-roles', 'rol-arcoiris', 'roles-arcoiris', 'rola'
    ])
    @commands.guild_only()
    async def rainbow_role(self, ctx, *args):
        if len(args) == 0:
            await self._list_server_rroles(ctx)
            return

        if not ctx.message.author.guild_permissions.manage_roles:
            await ctx.message.channel.send('No tienes suficientes poderes.')
            return

        options = args[1:]
        if args[0] in TEXTS['add']:
            action = 'add'
        elif args[0] in TEXTS['rm']:
            action = 'rm'
        elif args[0] in TEXTS['set']:
            action = 'set'
        else:
            action = None
            options = args[0:]

        options = ' '.join(options)
        options = yaml.load(options)
        if not isinstance(options, dict):
            await ctx.message.channel.send(
                'Debes enviarlo en formato objeto JSON. {"clave": "valor"}'
            )
            return

        role = await get_role(
            ctx.message.guild.roles,
            (await self._get_args(options, 'role'), )
        )
        if role is None:
            await ctx.message.channel.send('Debes indicar un rol válido.')
            return

        colours = await self._get_args(options, 'colour', iterable=True)

        current_roles = await self._get_current_roles(ctx.message.guild.id)

        if (action == 'set' or ((action == 'add' or action is None) \
                and role.id not in current_roles)) \
                and (colours is None or len(colours) < 2):
            await ctx.message.channel.send(
                'Para esta acción debes indicar al menos dos colores.'
            )
            return

        if (action == 'rm' or (action is None and role.id in current_roles)) \
                 and len(colours) == 0:
            await self._remove_rrole(ctx.message.guild.id, role.id)
            await ctx.message.channel.send('Rol Arcoiris eliminado.')
            return

        interval = await self._get_args(options, 'interval', default=5)

        role_colours = await self._get_current_colours(
            ctx.message.guild.id,
            role.id
        )

        if action == 'set':
            role_colours = colours
        else:
            for colour in colours:
                if not isinstance(colour, int):
                    await ctx.message.channel.send(
                        'Debes introducir los colores en formato Hex.'
                    )
                    return
                if (action == 'add' or action is None) and \
                        colour not in role_colours:
                    role_colours.append(colour)
                elif (action == 'rm' or action is None) and \
                        colour in role_colours:
                    role_colours.remove(colour)

        if (action in ('add', 'set') or action is None) and \
                role.id not in current_roles:
            await self._add_rrole(
                ctx.message.guild.id,
                role.id,
                role_colours,
                interval
            )
            msg = 'Rol Arcoiris añadido.'
        elif len(role_colours) < 2:
                await self._remove_rrole(ctx.message.guild.id, role.id)
                msg = 'Rol Arcoiris eliminado.'
        else:

            await self._edit_rrole(
                ctx.message.guild.id,
                role.id,
                role_colours,
                interval
            )
            msg = 'Rol Arcoiris editado.'

        await ctx.message.channel.send(msg)

    async def _list_server_rroles(self, ctx):
        roles = await self._get_all_roles(ctx.message.guild.id)
        fields = []
        for role in roles:
            _, role_id, _, colours, interval, _ = role
            role = await get_role(ctx.message.guild.roles, (role_id, ))
            if role is None:
                continue
            interval_text = f'**Intervalo**: {interval}s.'
            colours_text = f'**Colores**: {[hex(c) for c in colours]}.'
            fields.append(
                {
                    'name': u'\U0001F320'+f' {role.name}',
                    'value': f'{interval_text}\n{colours_text}',
                    'inline': True
                }
            )
        random_colour_index = randint(0, len(RAINBOW_COLOURS)-1)
        embed_colour = RAINBOW_COLOURS[random_colour_index]
        embed = await get_embed(
            ctx,
            title=u'\U0001F308'+' Roles Arcoiris',
            description='Lista de roles arcoiris para el servidor.',
            colour=embed_colour,
            thumbnail='https://i.imgur.com/wTPKlqg.jpg',
            footer={
                'text': (
                    f'Lista solicitada por {ctx.message.author.display_name} '
                    f'({ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=fields
        )
        list_msg = await ctx.message.channel.send(embed=embed)

        await asyncio.sleep(5)
        stop_datetime = datetime.now() + timedelta(minutes=2)
        while datetime.now() <= stop_datetime:
            i = RAINBOW_COLOURS.index(embed_colour) + 1
            embed_colour = RAINBOW_COLOURS[i % len(RAINBOW_COLOURS)]
            embed.colour = embed_colour
            await list_msg.edit(embed=embed)
            await asyncio.sleep(5)

    async def _add_rrole(self, guild_id, role_id, colours, interval):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['insert_rrole'],
            (guild_id, role_id, colours, interval)
        )
        conn.commit()
        cur.close()
        conn.close()

    async def _edit_rrole(self, guild_id, role_id, colours, interval):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['update_rrole'],
            (colours, interval, guild_id, role_id)
        )
        conn.commit()
        cur.close()
        conn.close()

    async def _remove_rrole(self, guild_id, role_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(DB_QUERIES['remove_rrole'], (guild_id, role_id))
        conn.commit()
        cur.close()
        conn.close()

    async def _get_args(self, args, name, default=None, iterable=False):
        field = None
        for field_indicator in TEXTS[f'{name} indicator']:
            field = args.get(field_indicator, None)
            if field is not None:
                break
        field = field if field else default
        if iterable and not isinstance(field, list):
            if field is None:
                field = []
            else:
                field = [field]
        return field

    async def _get_all_roles(self, guild_id):
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(DB_QUERIES['select_rrole_data'], (guild_id, ))
            roles = cur.fetchall()
        except:
            conn.rollback()
            cur.execute(DB_QUERIES['create_rrole_table'])
            roles = []
        conn.commit()
        cur.close()
        conn.close()
        return roles

    async def _get_current_roles(self, guild_id):
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(DB_QUERIES['select_rrole_id'], (guild_id, ))
            roles = cur.fetchall()
            roles = [r[0] for r in roles]
        except:
            conn.rollback()
            cur.execute(DB_QUERIES['create_rrole_table'])
            roles = []
        conn.commit()
        cur.close()
        conn.close()
        return roles

    async def _get_current_colours(self, guild_id, role_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(DB_QUERIES['select_rrole_colours'], (guild_id, role_id))
        colours = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return colours[0] if colours else []
