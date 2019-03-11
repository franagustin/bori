import yaml
from discord.ext import commands
from utils import BaseCommand, db_connect, get_embed, get_prefixes

DB_QUERIES = yaml.load(open('data/db_queries.yml'))


class Prefix(BaseCommand):
    @commands.command(name='prefijo', aliases=[
        'prefijos', 'prefix', 'prefixes'
    ])
    async def prefix(self, ctx, action=None, action_prefix=None):
        """Maneja el flujo del comando *prefijo*. Llama a la función adecuada
        según se quiera añadir uno, eliminar uno o establecer uno como único
        disponible.
        """
        add_actions = {
            'añadir', 'añade', 'agrega', 'agregar', 'nuevo', 'poner', 'pon',
            'add', 'new', 'put'
        }
        rm_actions = {
            'quitar', 'quita', 'sacar', 'saca', 'eliminar', 'elimina',
            'remove', 'rm'
        }
        set_actions = {
            'establecer', 'establece', 'unico', 'único', 'solo', 'sólo',
            'set', 'only'
        }
        if action in add_actions:
            if action_prefix is None:
                await ctx.message.channel.send(
                    'Debes introducir un nuevo prefijo.'
                )
            else:
                await self._add_prefix(ctx, action_prefix)
        elif action in rm_actions:
            if action_prefix is None:
                await self._set_prefix(ctx, 'g$')
            else:
                await self._remove_prefix(ctx, action_prefix)
        elif action in set_actions:
            if action_prefix is None:
                action_prefix = 'g$'
            await self._set_prefix(ctx, action_prefix)
        else:
            await self._list_prefixes(ctx)
        
    async def _list_prefixes(self, ctx):
        """Consulta la base de datos y devuelve los prefijos disponibles
        en el servidor en forma de embed.
        """
        prefixes = await get_prefixes(ctx.message.guild.id)
        prefixes = '\n'.join(prefixes)
        prefix_embed = await get_embed(
            ctx,
            title=u'\U00002699'+' Prefijos',
			description='Lista de prefijos actuales para este servidor.',
            colour=0x2464CC,
            thumbnail=self.bot.user.avatar_url,
            footer={
                'text': (
                    'Lista solicitada por '
                    f'{ctx.message.author.display_name} ('
                    f'{ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=(
                {
                    'name': 'Prefijos (uno por línea)',
                    'value': prefixes,
                    'inline': False
                },
            )
        )        
        await ctx.message.channel.send(embed=prefix_embed)

    async def _add_prefix(self, ctx, new_prefix):
        """Añade un prefijo nuevo a la lista de prefijos disponibles,
        editando la base de datos. Avisa si el prefijo ya está incluido.
        """
        prefixes = await get_prefixes(ctx.message.guild.id)
        if new_prefix in prefixes:
            await ctx.message.channel.send('Ya está ese prefijo.')
        else:
            conn = db_connect()
            cur = conn.cursor()
            cur.execute(
                DB_QUERIES['update_prefixes'],
                (prefixes+[new_prefix], ctx.message.guild.id)
            )
            conn.commit()
            cur.close()
            conn.close()
            await ctx.message.channel.send(
                f'**{new_prefix}** ha sido añadido como prefijo.'
            )

    async def _remove_prefix(self, ctx, rm_prefix):
        """Quita un prefijo de la base de datos, volviéndolo inutilizable
        para el servidor.
        No permite quitarlo si es el único que existe.
        """
        prefixes = await get_prefixes(ctx.message.guild.id)
        if rm_prefix not in prefixes:
            await ctx.message.channel.send('Ese prefijo no está actualmente.')
        elif len(prefixes) == 1:
            await ctx.message.channel.send(
                'No puedes quitar el único prefijo.'
            )
        else:
            prefixes.remove(rm_prefix)
            conn = db_connect()
            cur = conn.cursor()
            cur.execute(
                DB_QUERIES['update_prefixes'],
                (prefixes, ctx.message.guild.id)
            )
            conn.commit()
            cur.close()
            conn.close()
            await ctx.message.channel.send(
                f'**{rm_prefix}** ha sido eliminado correctamente.'
            )
        
    async def _set_prefix(self, ctx, prefix):
        """Establece un prefijo como el único disponible para el servidor."""
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['update_prefixes'],
            ([prefix], ctx.message.guild.id)
        )
        conn.commit()
        cur.close()
        conn.close()
        await ctx.message.channel.send(
            f'**{prefix}** ha sido establecido como el único '
            'prefijo para el server.'
        )
