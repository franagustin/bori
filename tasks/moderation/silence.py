import asyncio
import yaml
from datetime import datetime
from utils import BaseTask, db_connect, get_embed, get_member, get_muted_role

DB_QUERIES = yaml.load(open('data/db_queries.yml'))


class UnmuteTaskLoop(BaseTask):
    async def unmute(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                await self._autounmute_guild_members(guild)
            await asyncio.sleep(1)


    async def _autounmute_guild_members(self, guild):
        muted_role = await get_muted_role(guild.roles)
        if muted_role is None:
            return
        conn = db_connect()
        cur = conn.cursor()
        try:
            cur.execute(DB_QUERIES['select_all_muted'], (guild.id,))
            muted_members = cur.fetchall()
        except:
            muted_members = []
        for member_data in muted_members:
            if datetime.utcnow() > member_data[3]:
                cur.execute(
                    DB_QUERIES['remove_muted'],
                    (guild.id, member_data[2])
                )
                conn.commit()
                await self._send_unmute_embed(guild, member_data[2])
                await self._send_unmute_embed(guild, member_data[2], True)
                member = await get_member(guild.members, member_data[2])
                if member is not None and muted_role in member.roles:
                    await member.remove_roles(
                        muted_role,
                        reason="Unmute Task."
                    )
        cur.close()
        conn.close()

    async def _send_unmute_embed(self, guild, member_id, is_private=False):
        member = await get_member(guild.members, member_id)
        if member is None:
            return
        if not is_private and guild.system_channel is None:
            return
        unmute_embed = await self._get_unmute_embed(
            guild,
            member,
            is_private
        )
        if not is_private:
            await guild.system_channel.send(embed=unmute_embed)
            return
        try:
            await member.send(embed=unmute_embed)
        except:
            pass

    async def _get_unmute_embed(self, guild, member, is_private=False):
        title = u'\U0001F50A '
        colour = 0xFFFF00
        reason_field={
            'name': u'\U0001F5DE '+'Razón',
            'value': 'Transcurrió el tiempo de silencio.',
            'inline': False
        }
        if is_private:
            title += guild.name
            description = (
                f'Has sido desilenciado en **{guild.name}** y ya puedes '
                'hablar de nuevo.'
            )
            thumbnail = guild.icon_url
            footer = None
            fields = (
                reason_field,
                {
                    'name': u'\U0001F46E '+'Usuario',
                    'value': (
                        f'Fuiste desilenciado por **{self.bot.user.name}** ('
                        f'*{self.bot.user.name}#'
                        f'{self.bot.user.discriminator}*)'
                    ),
                    'inline': False
                }
            )
        else:
            title += 'Usuario Desilenciado'
            description = (
                'Un usuario ha sido **desilenciado** en el servidor.'
            )
            thumbnail = member.avatar_url
            footer = {
                'text': (
                    'Este usuario fue desilenciado automáticamente por '
                    f'{self.bot.user.name} ({self.bot.user.name}#'
                    f'{self.bot.user.discriminator})'
                ),
                'icon': self.bot.user.avatar_url
            }
            fields = (
                {
                    'name': u'\U0001F910 '+'Usuario',
                    'value': (
                        f'**{member.display_name}** (*{member.name}#'
                        f'{member.discriminator}*)'
                    ),
                    'inline': False
                },
                reason_field
            )
        return await get_embed(
            None,
            title=title,
            description=description,
            colour=colour,
            thumbnail=thumbnail,
            footer=footer,
            fields=fields
        )
