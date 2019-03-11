import yaml
from datetime import datetime, timedelta
from discord.ext import commands
from utils import (
    BaseCommand, db_connect, get_embed, get_member, get_muted_role,
    NUMBER_PATTERN, TIME_PATTERN
)

DB_QUERIES = yaml.load(open('data/db_queries.yml'))
TEXTS = yaml.load(open('data/texts/moderation.yml'))
NO_REASON = 'No se ha especificado una razón.'


class Silence(BaseCommand):
    @commands.command(name='mute', aliases=[
        'silencio', 'silenciar', 'silencia',
    ])
    @commands.guild_only()
    async def mute(self, ctx, member, *args):
        if not ctx.message.author.guild_permissions.kick_members and \
                not ctx.message.author.guild_permissions.manage_roles:
            await ctx.message.channel.send('No tienes suficientes permisos.')
            return
        member = await get_member(ctx.message.guild.members, member)
        if member is None:
            await ctx.message.channel.send('Debes indicar un miembro.')
            return
        muted_role = await get_muted_role(ctx.message.guild.roles)
        if muted_role is None:
            await ctx.message.channel.send(TEXTS['no mute role'])
            return
        time = '10'
        if len(args) >= 1 and len(args[0]) == 1:
            if TIME_PATTERN.match(args[0]) and len(args[0]) == 1:
                time = args[0]
                args = args[1:]
            elif TIME_PATTERN.match(args[-1]) and len(args[-1]) == 1:
                time = args[-1]
                args = args[:-1]
        elif len(args) >= 1:
            if TIME_PATTERN.match(args[0]) and \
                    NUMBER_PATTERN.match(args[0][:-1]):
                time = args[0]
                args = args[1:]
            elif TIME_PATTERN.match(args[-1]) and \
                    NUMBER_PATTERN.match(args[-1][:-1]):
                time = args[-1]
                args = args[:-1]
        reason = ' '.join(args) if len(args) >= 1 else NO_REASON
        if time.endswith('s'):
            time_text = 'segundos'
            time = time[:-1]
            add_time = timedelta(seconds=int(time))
        elif time.endswith('m'):
            time_text = 'minutos'
            time = time[:-1]
            add_time = timedelta(minutes=int(time))
        elif time.endswith('h'):
            time_text = 'horas'
            time = time[:-1]
            add_time = timedelta(hours=int(time))
        elif time.endswith('d'):
            time_text = 'días'
            time = time[:-1]
            add_time = timedelta(days=int(time))
        elif time.endswith('w'):
            time_text = 'semanas'
            time = time[:-1]
            add_time = timedelta(weeks=int(time))
        elif time.endswith('a') or time.endswith('y'):
            time_text = 'años'
            time = time[:-1]
            add_time = timedelta(days=365*int(time))
        elif time.endswith('c'):
            time_text= 'siglos'
            time = time[:-1]
            add_time = timedelta(days=100*365*int(time))
        else:
            time_text = 'minutos'
            add_time = timedelta(minutes=int(time))
        end_time = datetime.utcnow() + add_time
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(
                DB_QUERIES['select_muted'],
                (ctx.message.guild.id, member.id)
            )
            is_muted = cur.fetchone() is not None
            if is_muted:
                cur.execute(
                    DB_QUERIES['update_muted'],
                    (end_time, ctx.message.guild.id, member.id)
                )
            else:
                cur.execute(
                    DB_QUERIES['insert_muted'],
                    (ctx.message.guild.id, member.id, end_time)
                )
        except:
            cur.execute(DB_QUERIES['create_muted_table'])
            cur.execute(
                DB_QUERIES['insert_muted'],
                (ctx.message.guild.id, member.id, end_time)
            )
        conn.commit()
        cur.close()
        conn.close()
        await member.add_roles(muted_role, reason="Mute command.")
        muted_embed = await get_embed(
            ctx,
            title=u'\U0001F507 '+'Usuario Silenciado',
            description='Un usuario ha sido **silenciado** en el servidor.',
            colour=0xFFFF00,
            thumbnail=member.avatar_url,
            footer={
                'text': (
                    'Este usuario fue silenciado por '
                    f'{ctx.message.author.display_name} ('
                    f'{ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=(
                {
                    'name': u'\U0001F910 '+'Usuario',
                    'value': (
                        f'**{ctx.message.author.display_name}** ('
                        f'*{ctx.message.author.name}#'
                        f'{ctx.message.author.discriminator}*)'
                    ),
                    'inline': False
                },
                {
                    'name': u'\U0001F5DE '+'Razón',
                    'value': reason,
                    'inline': False
                },
                {
                    'name': u'\U000023F0 '+'Tiempo',
                    'value': (
                        f'La duración del silencio es de **{time}** '
                        f'{time_text}.'
                    ),
                    'inline': False
                }
            )
        )
        await ctx.message.channel.send(embed=muted_embed)
        if member == ctx.message.author or member.bot:
            return
        try:
            member_muted_embed = await get_embed(
                ctx,
                title=u'\U0001F910 '+ctx.message.guild.name,
                description=(
                    f'Has sido silenciado en **{ctx.message.guild.name}** '
                    'y no puedes hablar hasta nuevo aviso.'
                ),
                colour=0xFFFF00,
                thumbnail=ctx.message.guild.icon_url,
                fields=(
                    {
                        'name': u'\U000023F0 '+'Tiempo',
                        'value': (
                            f'La duración del silencio es de **{time}** '
                            f'{time_text}.'
                        ),
                        'inline': False
                    },
                    {
                        'name': u'\U0001F5DE '+'Razón',
                        'value': reason,
                        'inline': False
                    },
                    {
                        'name': u'\U0001F46E '+'Usuario',
                        'value': (
                            'Fuiste silenciado por '
                            f'**{ctx.message.author.display_name}** ('
                            f'*{ctx.message.author.name}#'
                            f'{ctx.message.author.discriminator}*)'
                        ),
                        'inline': False
                    }
                )
            )
            await member.send(embed=member_muted_embed)
        except:
            pass


    @commands.command(name='unmute', aliases=[
        'desilencio', 'desilenciar', 'desilencia'
    ])
    @commands.guild_only()
    async def unmute(self, ctx, member, *reason):
        if not ctx.message.author.guild_permissions.kick_members and \
                not ctx.message.author.guild_permissions.manage_roles:
            await ctx.message.channel.send('No tienes suficientes permisos.')
            return
        member = await get_member(ctx.message.guild.members, member)
        if member is None:
            await ctx.message.channel.send('Tienes que indicar un miembro.')
            return
        muted_role = await get_muted_role(ctx.message.guild.roles)
        if muted_role is None:
            await ctx.message.channel.send(TEXTS['no mute role'])
            return
        reason = " ".join(reason) if len(reason) >= 1 else NO_REASON
        not_muted = 'Ese miembro no está silenciado.'
        msg = None
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(
                DB_QUERIES['select_muted'],
                (ctx.message.guild.id, member.id)
            )
            is_muted = cur.fetchone() is not None
            if is_muted:
                cur.execute(
                    DB_QUERIES['remove_muted'],
                    (ctx.message.guild.id, member.id)
                )
                conn.commit()
            else:
                msg = not_muted
        except:
            conn.rollback()
            msg = not_muted
        cur.close()
        conn.close()
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Unmute command.")
        if msg is not None:
            await ctx.message.channel.send(msg)
            return
        unmute_embed = await get_embed(
            ctx,
            title=u'\U0001F50A '+'Usuario Desilenciado',
            description=(
                'Un usuario ha sido **desilenciado** en el servidor.'
            ),
            colour=0xFFFF00,
            thumbnail=member.avatar_url,
            footer={
                'text': (
                    'Este usuario fue desilenciado por '
                    f'{ctx.message.author.display_name} ('
                    f'{ctx.message.author.name}#'
                    f'{ctx.message.author.discriminator})'
                ),
                'icon': ctx.message.author.avatar_url
            },
            fields=(
                {
                    'name': u'\U0001F910 '+'Usuario',
                    'value': (
                        f'**{ctx.message.author.display_name}** ('
                        f'*{ctx.message.author.name}#'
                        f'{ctx.message.author.discriminator}*)'
                    ),
                    'inline': False
                },
                {
                    'name': u'\U0001F5DE '+'Razón',
                    'value': reason,
                    'inline': False
                }
            )
        )
        await ctx.message.channel.send(embed=unmute_embed)
        if member == ctx.message.author or member.bot:
            return
        try:
            unmute_member_embed = await get_embed(
                ctx,
                title=u'\U0001F50A '+ctx.message.guild.name,
                description=(
                    f'Has sido desilenciado en **{ctx.message.guild.name}** '
                    'y ya puedes hablar de nuevo.'
                ),
                colour=0xFFFF00,
                thumbnail=ctx.message.guild.icon_url,
                fields=(
                    {
                        'name': u'\U0001F5DE '+'Razón',
                        'value': reason,
                        'inline': False
                    },
                    {
                        'name': u'\U0001F46E '+'Usuario',
                        'value': (
                            'Fuiste silenciado por '
                            f'**{ctx.message.author.display_name}** ('
                            f'*{ctx.message.author.name}#'
                            f'{ctx.message.author.discriminator}*)'
                        ),
                        'inline': False
                    }
                )
            )
            await member.send(embed=member_muted_embed)
        except:
            pass


    async def _on_member_join_mute(self, member):
        muted_role = await get_muted_role(member.guild.roles)
        if muted_role is None:
            return
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(
                DB_QUERIES['select_muted'],
                (member.guild.id, member.id)
            )
            muted = cur.fetchone()
            if member.id == muted[2]:
                await member.add_roles(muted_role, reason="Mute on join.")
        except:
            pass
        cur.close()
        conn.close()
