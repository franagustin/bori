import dataclasses

from discord import Embed, Guild, Member
from discord.ext.commands import Bot, Cog, command, Context

from utils.guild_utils import get_author_string


BOT_INVITE_URL = (
    'https://discordapp.com/api/oauth2/authorize?client_id={}'
    '&permissions=1543825495&scope=bot'
)

THUMBNAIL_URL = (
    'https://cdn0.iconfinder.com/data/icons/party-and-celebrations-8/128/242-512.png'
)


@dataclasses.dataclass(eq=False)
class Invitation(Cog):
    bot: Bot

    @command(name='invitation', aliases=['invite', 'invitar', 'invitacion', 'invitación'])
    async def invitation(self, ctx: Context, guild: Guild = None):
        """Invite me to your server!"""
        if guild is not None:
            await ctx.message.channel.send('Not implemented yet!')
            return

        invite_embed = await self._build_embed(ctx.message.author)
        await ctx.message.channel.send(embed=invite_embed)

    async def _build_embed(self, author: Member):
        bot_invite_url = BOT_INVITE_URL.format(self.bot.user.id)
        embed = Embed(
            title=u'\U0001F4E9'+' Invitación',
            description=f'[Invítame a tu server]({bot_invite_url}).',
            colour=0xFA3E7D,
        )
        embed.set_thumbnail(url=THUMBNAIL_URL)
        embed.set_footer(
            text=f'Invitación solicitada por {get_author_string(author)}.',
            icon_url=author.avatar_url
        )
        return embed
