import discord
import yaml
from datetime import datetime, timedelta
from discord.ext import commands
from utils import (
    BaseCommand, get_member, get_role, db_connect, get_embed, TIME_PATTERN,
    NUMBER_PATTERN, get_muted_role
)
DB_QUERIES = yaml.load(open('data/db_queries.yml'))
TEXTS = yaml.load(open('data/texts/moderation.yml'))
NO_REASON = 'No se ha especificado una razón.'


class Moderation(BaseCommand):
    @commands.command(name='nick', aliases=['apodo', 'nickname'])
    @commands.guild_only()
    async def nickname(self, ctx, member, *args):
        manage_nicks = ctx.message.author.guild_permissions.manage_nicknames
        change_nick = ctx.message.author.guild_permissions.change_nickname
        member = await get_member(ctx.message.guild.members, member)
        if member is None:
            await ctx.message.channel.send('Debes indicar un miembro del servidor.')
            return
        elif (member != ctx.message.author and not manage_nicks) or \
                (member == ctx.message.author and not change_nick):
            await ctx.message.channel.send('No tienes los permisos suficientes.')
            return
        new_nick = " ".join(args) if len(args) >= 1 else None
        await member.edit(
            nick=new_nick,
            reason='Nickname change command.'
        )
        new_nick = member.name if new_nick is None else new_nick
        await ctx.message.channel.send(
            f'El nuevo nick para *{member.name}#{member.discriminator}* es '
            f'**{new_nick}**'
        )
    
    
    @commands.command(name='rol', aliases=['roles', 'role'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, *args):
        if len(args) < 2:
            await ctx.message.channel.send('Debes indicar miembro y rol.')
            return
        member_search = args[1]
        role_search = args[2:]
        if args[0] in TEXTS['add']:
            action = 'add'
        elif args[0] in TEXTS['rm']:
            action = 'rm'
        elif args[0] in TEXTS['set']:
            action = 'set'
        else:
            action = None
            member_search = args[0]
            role_search = args[1:]
        member = await get_member(ctx.message.guild.members, member_search)
        if member is None:
            await ctx.message.channel.send('Debes indicar un miembro válido.')
            return
        role = await get_role(ctx.message.guild.roles, role_search)
        if role is None:
            await ctx.message.channel.send('Debes indicar un rol válido.')
            return
        if action is None and role in member.roles:
            action = 'rm'
        elif action is None:
            action = 'add'
        if action == 'add':
            if role in member.roles:
                await ctx.message.channel.send(
                    f'{member.display_name} ya tiene el rol {role.name}.'
                )
                return
            await member.add_roles(role, reason='Role add command.')
            await ctx.message.channel.send(
                f'A {member.display_name} se la ha concedido el rol '
                f'{role.name}.'
            )
        elif action == 'rm':
            if role not in member.roles:
                await ctx.message.channel.send(
                    f'{member.display_name} no tiene el rol {role.name}.'
                )
                return
            await member.remove_roles(role, reason='Role remove command.')
            await ctx.message.channel.send(
                f'A {member.display_name} se le ha quitado el rol '
                f'{role.name}.'
            )
        else:
            await member.edit(roles=[role], reason='Role set command.')
            await ctx.message.channel.send(
                f'Se ha establecido {role.name} como el único rol de '
                f'{member.display_name}.'
            )

        
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


    @commands.command(name='persistent-role', aliases=[
        'persistent_role', 'prole', 'per-role',
        'rol-persistente', 'rol_persistente', 'rolp', 'prol', 'rol-per'
    ])
    @commands.guild_only()
    async def persistent_role(self, ctx, *args):
        if len(args) < 1:
            await self._list_server_proles(ctx)
            return
        elif not ctx.message.author.guild_permissions.manage_roles:
            await ctx.message.channel.send('No tienes suficientes permisos.')
            return
        role_start = 1
        if args[0] in TEXTS['add']:
            action = 'add'
        elif args[0] in TEXTS['rm']:
            action = 'rm'
        elif args[0] in TEXTS['set']:
            action = 'set'
        else:
            action = None
            role_start = 0
        members = None
        for member_indicator in TEXTS['prole members']:
            try:
                i = args.index(member_indicator)
                role_search = args[role_start:i]
                members = args[i+1:]
                break
            except IndexError:
                await ctx.message.channel.send('Debes indicar un rol.')
                return
            except ValueError:
                pass
        if members is None:
            if action == 'set':
                await ctx.message.channel.send(
                    'Para esta acción debes indicar miembros.'
                )
                return
            role_search = args[role_start:]
            members = []
        role = await get_role(ctx.message.guild.roles, role_search)
        if role is None:
            await ctx.message.channel.send('Debes indicar un rol válido.')
            return
        current_roles = await self._get_server_proles(ctx.message.guild.id)
        if len(members) == 0:
            if role.id in current_roles and \
                    (action == 'rm' or action is None):
                await self._remove_prole(ctx.message.guild.id, role.id)
                msg = 'Rol persistente eliminado.'
            elif role.id not in current_roles and \
                    (action == 'add' or action is None):
                await self._add_prole(ctx.message.guild.id, role.id)
                msg = 'Rol persistente añadido.'
            else:
                await ctx.message.channel.send(
                    'Para esta acción debes indicar al menos un miembro.'
                )
                return
            await ctx.message.channel.send(msg)
            return
        if len(members) == 1:
            if members[0].lower() in ('everyone', 'all', 'todos'):
                print(True)
                member_ids = [0]
            elif members[0].lower() in ('humans', 'humanos', '!bots'):
                member_ids = [1]
            elif members[0].lower() in ('bots', '!humans', '!humanos'):
                member_ids = [2]
            elif members[0].lower() in ('!everyone', '!all', '!todos'):
                await self._remove_prole(ctx.message.guild.id, role.id)
                await ctx.message.channel.send('Rol persistente eliminado.')
                return
        else:
            member_ids = await self._get_new_member_ids(
                ctx.message.guild,
                role.id,
                action,
                members
            )
            if member_ids is None:
                await ctx.message.channel.send(
                    'Debes indicar un miembro válido.'
                )
                return
        conn = db_connect()
        cur = conn.cursor()
        if role.id in current_roles:
            cur.execute(
                DB_QUERIES['update_prole'],
                (member_ids, ctx.message.guild.id, role.id)
            )
        else:
            cur.execute(
                DB_QUERIES['insert_prole'],
                (ctx.message.guild.id, member_ids, role.id)
            )
        conn.commit()
        cur.close()
        conn.close()
        await ctx.message.channel.send('Acción finalizada correctamente.')

    async def _on_member_join_proles(self, member):
        proles = await self._get_server_proles_in_use(member.guild.id)
        for data in proles:
            role = await get_role(member.guild.roles, (data[0],))
            if role is None:
                return
            if data[1][0] == 0 or (data[1][0] == 1 and not member.bot) or \
                    (data[1][0] == 2 and member.bot) or member.id in data[1]:
                await member.add_roles(role, reason="Persistent role.")

    async def _list_server_proles(self, ctx):
        roles = await self._get_server_proles_in_use(ctx.message.guild.id)
        fields = []
        for data in roles:
            role = await get_role(ctx.message.guild.roles, (data[0],))
            if role is None:
                continue
            members = []
            if data[1][0] == 0:
                members = ['**Everyone**']
            elif data[1][0] == 1:
                memebrs = ['**Humans**']
            elif data[1][0] == 2:
                members = ['**Bots**']
            else:
                for member_id in data[1]:
                    member = await get_member(
                        ctx.message.guild.members, member_id
                    )
                    if member is not None:
                        members.append(member)
                members = [m.display_name for m in members]
            if len(members) == 0:
                continue
            fields.append({
                'name': role.name,
                'value': "- "+"\n- ".join(members),
                'inline': False
            })
        list_embed = await get_embed(
            ctx,
            title=u'\U0001F947 '+'Roles Persistentes',
            description='Lista de roles persistentes para el servidor.',
            colour=0xFFA500,
            thumbnail=ctx.message.guild.icon_url,
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
        await ctx.message.channel.send(embed=list_embed)
    
    async def _add_prole(self, guild_id, role_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(DB_QUERIES['insert_prole'], (guild_id, [0], role_id))
        conn.commit()
        cur.close()
        conn.close()

    async def _remove_prole(self, guild_id, role_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(DB_QUERIES['remove_prole'], (guild_id, role_id))
        conn.commit()
        cur.close()
        conn.close()

    async def _get_server_proles(self, guild_id):
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(DB_QUERIES['select_server_proles'], (guild_id,))
            roles = cur.fetchall()
            roles = [r[0] for r in roles]
        except:
            conn.rollback()
            cur.execute(DB_QUERIES['create_prole_table'])
            conn.commit()
            roles = []
        cur.close()
        conn.close()
        return roles

    async def _get_server_proles_in_use(self, guild_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['select_filled_server_proles'],
            (guild_id,)
        )
        roles = cur.fetchall()
        return roles
    
    async def _get_members_for_prole(self, guild_id, role_id):
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(DB_QUERIES['get_members_prole'], (guild_id, role_id))
            members = cur.fetchone()[0]
        except:
            conn.rollback()
            cur.execute(DB_QUERIES['insert_prole'], (guild_id, [], role_id))
            conn.commit()
            members = None
        if members is None:
            members = []
        cur.close()
        conn.close()
        return members

    async def _get_new_member_ids(self, guild, role_id, action, members):
        member_list = []
        for member in members:
            member = await get_member(guild.members, member)
            if member is not None:
                member_list.append(member)
        if len(member_list) == 0:
            return
        member_ids = [m.id for m in member_list]
        members = await self._get_members_for_prole(guild.id, role_id)
        if action == 'set':
            members = member_ids
        else:
            for member_id in member_ids:
                if member_id in members and \
                        (action == 'rm' or action is None):
                    members.remove(member_id)
                elif member_id not in members and \
                        (action == 'add' or action is None):
                    members.append(member_id)
        return members


    @commands.Cog.listener()
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


def setup(bot):
    bot.add_cog(Moderation(bot))
