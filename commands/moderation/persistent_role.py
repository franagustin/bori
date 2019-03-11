import yaml
from discord.ext import commands
from utils import BaseCommand, db_connect, get_embed, get_member, get_role

DB_QUERIES = yaml.load(open('data/db_queries.yml'))
TEXTS = yaml.load(open('data/texts/moderation.yml'))


class PersistentRole(BaseCommand):
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
