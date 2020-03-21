import asyncio
import discord
import yaml
from datetime import datetime, timedelta
from utils import BaseTask, db_connect, get_role


DB_QUERIES = yaml.load(open('data/db_queries.yml'))


class RainbowRoleTaskLoop(BaseTask):
    async def change_role_colour(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                try:
                    await self._change_role_colour_for_guild(guild)
                except:
                    pass
            await asyncio.sleep(5)

    async def _change_role_colour_for_guild(self, guild):
        roles = await self._get_rainbow_roles(guild.id)
        for role_data in roles:
            _, role_id, _, colours, interval, last_edited = role_data
            if datetime.now() < last_edited + timedelta(seconds=interval):
                return

            role = await get_role(guild.roles, (role_id, ))
            try:
                i = (colours.index(role.colour.value) + 1) % len(colours)
            except ValueError:
                i = 0
            await role.edit(colour=discord.Colour(colours[i]))
            conn = db_connect()
            cur = conn.cursor()
            cur.execute(
                DB_QUERIES['update_rrole_edited_time'],
                (datetime.now(), guild.id, role.id)
            )
            conn.commit()
            cur.close()
            conn.close()

    async def _get_rainbow_roles(self, guild_id):
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
