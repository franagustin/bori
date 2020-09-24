import dataclasses

from discord import Embed, Member
from discord.ext.commands import Bot, Cog, command, Context

from utils.datetime_utils import get_diff_milliseconds
from utils.guild_utils import get_author_string


@dataclasses.dataclass(eq=False)
class Ping(Cog):
    bot: Bot

    @command(name='ping')
    async def ping(self, ctx: Context):
        """Replies "Pong!", edits that message and then creates an embed stating
        the time elapsed until the first reply, the time taken to edit and the
        total time."""
        msg = ctx.message
        pong_msg = await msg.channel.send('Pong!')
        await pong_msg.edit(content=f'{pong_msg.content} `:EDIT:`')
        requested_time = msg.created_at
        ponged_time = pong_msg.created_at
        edited_time = pong_msg.edited_at
        reply_time = get_diff_milliseconds(ponged_time, requested_time)
        edit_time = get_diff_milliseconds(edited_time, ponged_time)
        total_time = get_diff_milliseconds(edited_time, requested_time)
        pong_embed = await self._build_embed(msg.author, reply_time, edit_time, total_time)
        await pong_msg.edit(content=None, embed=pong_embed)

    async def _build_embed(self, author: Member, reply_time: int, edit_time: int,
                           total_time: int) -> Embed:
        embed = Embed(
            title=u'\U0001F3D3'+' ¡Pong!',
            description='Me dices ping, te digo pong.',
            colour=0xDD2E44,
        )
        embed.set_thumbnail(url='https://i.imgur.com/QzF08A1.png')
        embed.set_footer(
            text=f'Este mensaje es una respuesta a {get_author_string(author)}',
            icon_url=author.avatar_url
        )
        embed.add_field(
            name=u'\U0001F54A' + ' Tiempo de respuesta',
            value=f'Respondí en: {reply_time}ms.',
            inline=False
        )
        embed.add_field(
            name=u'\U0000270F' + ' Tiempo de edición',
            value=f'Edité mi mensaje en: {edit_time}ms.',
            inline=False
        )
        embed.add_field(
            name=u'\U0001F4F0' + ' Tiempo total',
            value=f'Entre tu mensaje y mi edición pasaron: {total_time}ms.',
            inline=False
        )
        return embed
