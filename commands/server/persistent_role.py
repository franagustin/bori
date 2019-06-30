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
        if len(args) == 0:
            await self._list_server_proles(ctx)
            return

        if not ctx.message.author.guild_permissions.manage_roles:
            await ctx.message.channel.send('No tienes suficientes poderes.')
            return

        options = args[1:]
        action = None
        if args[0] in TEXTS['add']:
            action = 'add'
        elif args[0] in TEXTS['rm']:
            action = 'rm'
        elif args[0] in TEXTS['set']:
            action = 'set'
        else:
            options = args[0:]

        options = ' '.join(options)
        options = yaml.load(options)
        if not isinstance(options, dict):
            await ctx.message.channel.send(
                'Debes enviarlo en formato objeto JSON. {"clave": "valor"}'
            )
            return

        roles = await self._get_args('role', options)
        for i in range(len(roles)):
            roles[i] = await get_role(ctx.message.guild.roles, [roles[i]])
        members = await self._get_args('member', options, required=False)
        current_only = await self._get_args(
            'current',
            options,
            required=False
        )
        if len(current_only) > 0:
            current_only = current_only[0]
        else:
            current_only = False

        if len(members) == 0:
            if action == 'add':
                await self._insert_edit_proles(
                    ctx.message.guild.id,
                    roles,
                    [0],
                    action
                )
                await ctx.message.channel.send('Roles persistentes añadidos.')
                return
            elif action == 'rm':
                await self._remove_proles(ctx.message.guild.id, roles)
                await ctx.message.channel.send(
                    'Roles persistentes eliminados.'
                )
                return
            elif action == 'set':
                await ctx.message.channel.send(
                    'Debes indicar al menos un miembro para esta acción.'
                )
                return
            else:
                await self._toggle_proles(ctx.message.guild.id, roles)
                await ctx.message.channel.send(
                    'Roles persistentes alterados con éxito.'
                )
                return

            await ctx.message.channel.send(msg)

        member_ids = None
        if len(members) == 1:
            if members[0] in ('everyone', 'everybody', 'all', 'todos'):
                if current_only:
                    member_ids = [m.id for m in ctx.message.guild.members]
                else:
                    member_ids = [0]
            elif members[0] in ('humans', 'humanos', '!bots'):
                if current_only:
                    member_ids = [
                        m.id for m in 
                        filter(lambda x: not x.bot, ctx.message.guild.members)
                    ]
                else:
                    member_ids = [1]
            elif members[0] in ('bots', '!humans', '!humanos'):
                if current_only:
                    member_ids = [
                        m.id for m in 
                        filter(lambda x: x.bot, ctx.message.guild.members)
                    ]
                else:
                    member_ids = [2]
        if member_ids is None:
            for i in range(len(members)):
                members[i] = await get_member(
                    ctx.message.guild.members,
                    members[i]
                )
            member_ids = [m.id for m in members]

        await self._insert_edit_proles(
            ctx.message.guild.id,
            roles,
            member_ids,
            action
        )
        await ctx.message.channel.send('Acción realizada con éxito.')

    async def _on_member_join_proles(self, member):
        proles = await self._get_server_proles_in_use(member.guild.id)
        for data in proles:
            role = await get_role(member.guild.roles, (data[0],))
            if role is None:
                return
            if data[1][0] == 0 or (data[1][0] == 1 and not member.bot) or \
                    (data[1][0] == 2 and member.bot) or member.id in data[1]:
                await member.add_roles(role, reason="Persistent role.")

    async def _get_member_list(self, guild_id, role_id, action, member_ids):
        if member_ids[0] in (0, 1, 2):
            return member_ids
        prole_members = await self._get_members_for_prole(guild_id, role_id)
        if len(prole_members) > 0 and prole_members[0] in (0, 1, 2):
            prole_members = []
        for member in member_ids:
            if (action == 'add' or action is None) and \
                    member not in prole_members:
                prole_members.append(member)
            elif (action == 'rm' or action is None) and \
                    member in prole_members:
                prole_members.remove(member)
            elif action == 'set':
                prole_members = member_ids
        return prole_members

    async def _get_args(self, name, args, required=True):
        for name_indicator in TEXTS[f'{name} indicator']:
            if name_indicator in args.keys():
                field = args[name_indicator]
                if not isinstance(field, list):
                    field = [field]
                break
        else:
            if required:
                await ctx.message.channel.send('Debes indicar al menos un rol.')
                return
            field = []
        return field

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
                members = ['**Humans**']
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
            thumbnail='http://www.singlecolorimage.com/get/33fd8f/250x250',
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
    
    async def _add_prole(self, guild_id, members, role_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(DB_QUERIES['insert_prole'], (guild_id, members, role_id))
        conn.commit()
        cur.close()
        conn.close()

    async def _edit_prole(self, guild_id, member_ids, role_id):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            DB_QUERIES['update_prole'],
            (member_ids, guild_id, role_id)
        )
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

    async def _insert_edit_proles(self, guild_id, roles, member_ids, action):
        current_roles = await self._get_server_proles(guild_id)
        for role in roles:
            members = await self._get_member_list(
                guild_id,
                role.id,
                action,
                member_ids
            )
            if role.id not in current_roles:
                await self._add_prole(guild_id, members, role.id)
            else:
                await self._edit_prole(guild_id, members, role.id)

    async def _remove_proles(self, guild_id, roles):
        for role in roles:
            await self._remove_prole(guild_id, role.id)

    async def _toggle_proles(self, guild_id, roles):
        current_roles = await self._get_server_proles(guild_id)
        for role in roles:
            if role.id in current_roles:
                await self._remove_prole(guild_id, role.id)
            else:
                await self._add_prole(guild_id, [0], role.id)

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
