import asyncio
import yaml
import json
from discord.ext import commands
from utils import BaseCommand, db_connect, get_embed


DB_QUERIES = yaml.load(open('data/db_queries.yml'))
TEXTS = yaml.load(open('data/texts/democracy.yml'))


class Polls(BaseCommand):
    @commands.command(name='vote', aliases=[
        'polls', 'poll', 'votacion', 'votar', 'vota', 'encuesta', 'encuestas'
    ])
    @commands.guild_only()
    async def polls(self, ctx, *args):
        if len(args) > 0:
            if args[0] in ('check', 'see', 'chequea', 'chequear', 'ver',
                           've'):
                await self._check_poll(ctx, *args[1:])
                return
            elif args[0] in ('create', 'start', 'new', 'crear',
                             'comenzar', 'empezar', 'nueva'):
                await self._create_poll(ctx, *args[1:])
                return
            elif args[0] in ('close', 'closed', 'finish', 'end', 'cerrar',
                             'finalizar', 'terminar', 'fin'):
                await self._close_poll(ctx, *args[1:])
                return
            else:
                await self._vote_poll(ctx, *args)
        else:
            await self._check_poll(ctx, *args[1:])


    async def _create_poll(self, ctx, *args):
        permissions = ctx.message.author.guild_permissions
        if not permissions.manage_channels and not \
                permissions.manage_messages:
            await ctx.message.channel.send('No tienes permisos.')
            return

        options = ' '.join(args).split(';')
        if len(options) == 1:
            options = ' '.join(args).split('|')
        if len(options) == 1:
            options = ' '.join(args).split(',')

        current_poll = await self._get_current_poll(ctx.message.channel.id)
        if current_poll is not None:
            await ctx.message.channel.send(
                'Ya hay una encuesta en curso en este canal.'
            )
            return

        topic = next(filter(lambda x: 't:' in x, options), None)
        if topic is not None:
            options.remove(topic)
        topic = topic.replace('t:', '') if topic else TEXTS['no topic']

        if len(options) < 2:
            await ctx.message.channel.send(
                'Debes ingresar al menos dos opciones.'
            )
            return

        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['create_poll'],
            (
                ctx.message.channel.id,
                topic,
                options,
                [0 for i in range(len(options))],
                json.dumps([])
            )
        )
        poll_data = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        poll_embed = await self._get_poll_embed(ctx, poll_data)
        await ctx.message.channel.send(embed=poll_embed)

    async def _check_poll(self, ctx, *args):
        current_poll = await self._get_current_poll(ctx.message.channel.id)
        if current_poll is None:
            await ctx.message.channel.send(
                'No hay encuestas en curso en este canal.'
            )
            return

        poll_embed = await self._get_poll_embed(ctx, current_poll)
        poll_msg = await ctx.message.channel.send(embed=poll_embed)
        await asyncio.sleep(5)
        await poll_msg.delete()

    async def _close_poll(self, ctx, *args):
        permissions = ctx.message.author.guild_permissions
        if not permissions.manage_channels and not \
                permissions.manage_messages:
            await ctx.message.channel.send('No tienes permisos.')
            return

        current_poll = await self._get_current_poll(ctx.message.channel.id)
        if current_poll is None:
            await ctx.message.channel.send(
                'No hay encuestas en curso en este canal.'
            )
            return

        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['close_active_poll'],
            (ctx.message.channel.id, )
        )
        poll_data = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        poll_embed = await self._get_poll_embed(ctx, poll_data)
        await ctx.message.channel.send(embed=poll_embed)

    async def _vote_poll(self, ctx, *args):
        current_poll = await self._get_current_poll(ctx.message.channel.id)
        if current_poll is None:
            await ctx.message.channel.send(
                'No hay encuestas en curso en este canal.'
            )
            return

        options = current_poll[3]
        votes = current_poll[4]
        voters = current_poll[5]

        await ctx.message.delete()

        if args[0] in ('vote', 'votar', 'vota'):
            args = args[1:]
        try:
            i = int(args[0]) - 1
        except ValueError:
            voted = ' '.join(args)
            if voted in options:
                i = options.index(voted)
            else:
                await ctx.message.channel.send('Debes elegir una opción.')
                return
        else:
            if i > len(options) - 1:
                msg = await ctx.message.channel.send('Opción inválida.')
                await asyncio.sleep(2)
                await msg.delete()
                return

        voter = next(
            filter(lambda x: ctx.message.author.id == x['id'], voters), None
        )

        if voter is not None and voter['vote'] != i:
            old_i = voter['vote']
            votes[old_i] -= 1
        if voter is None or voter['vote'] != i:
            votes[i] += 1
            if voter is None:
                voters.append({'id': ctx.message.author.id, 'vote': i})
            else:
                voter['vote'] = i

        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['update_poll'],
            (votes, json.dumps(voters), ctx.message.channel.id)
        )
        conn.commit()
        cur.close()
        conn.close()

        msg = await ctx.message.channel.send('Voto registrado con éxito.')
        await asyncio.sleep(2)
        await msg.delete()

    async def _get_current_poll(self, channel_id):
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(DB_QUERIES['select_active_poll'], (channel_id, ))
            poll_data = cur.fetchone()
        except:
            conn.rollback()
            cur.execute(DB_QUERIES['create_democracy_table'])
            poll_data = None
        conn.commit()
        cur.close()
        conn.close()
        return poll_data

    async def _get_poll_embed(self, ctx, poll_data):
        _, _, topic, options, votes, _, active = poll_data

        author_text = (
            f'{ctx.message.author.display_name} ('
            f'{ctx.message.author.name}#'
            f'{ctx.message.author.discriminator})'
        )
        if active:
            footer_text = f'Resultados consultados por {author_text}.'
            sort_func = lambda x: x['i']
            sort_reverse = False
        else:
            footer_text = f'Votación finalizada por {author_text}.'
            sort_func = lambda x: x['votes']
            sort_reverse = True

        max_votes_index = votes.index(max(votes)) + 1

        votes_dict = [
            {'votes': votes[i], 'option': options[i], 'i': i + 1}
            for i in range(len(options))
        ]
        votes_dict.sort(key=sort_func, reverse=sort_reverse)

        results = ''
        for option in votes_dict:
            if option['i'] == max_votes_index:
                remark = '**'
            else:
                remark = ''
            results += (
                f"{remark}"
                f"{option['i']}) {option['option']}: {option['votes']}"
                f"{remark}"
                '\n'
            )

        return await get_embed(
            ctx,
            title=u"\U0001F5F3"+" Votación",
            description=topic,
            colour=0xCCD6DD,
            thumbnail="https://i.imgur.com/5LEqNv7.png",
            footer={
                'text': footer_text,
                'icon': ctx.message.author.avatar_url
            },
            fields=(
                {'name': 'Resultados', 'value': results, 'inline': False},
            )
        )
