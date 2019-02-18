import discord
from discord.ext import commands
from .utils import BaseCommand, get_embed


class Utility(BaseCommand):
    @commands.command()
    async def ping(self, ctx):
        """Comando *ping*. Responde *¡Pong!* y lo edita. Luego cambia ese
        mensaje por un embed que contenga el tiempo que tarda en responder,
        el tiempo que tarda en editar desde que responde y el tiempo total
        entre el primer mensaje y la edición.

		Parámetros: NINGUNO
		Sintaxis:
			{prefijo}ping
	    """
        msg = ctx.message
        pong_msg = await msg.channel.send('¡Pong!')
        requested_time = msg.created_at
        ponged_time = pong_msg.created_at
        reply_time = self.get_milliseconds(ponged_time - requested_time)
        await pong_msg.edit(content=(
            f'{pong_msg.content} '
            f'`:{reply_time}:`'
            )
        )
        edited_time = pong_msg.edited_at
        edit_time = self.get_milliseconds(edited_time - ponged_time)
        total_time = self.get_milliseconds(edited_time - requested_time)
        pong_embed=get_embed(
            title=u'\U0001F3D3'+' ¡Pong!',
			description='Me dices ping, te digo pong.',
			colour=0xDD2E44,
            thumbnail='https://i.imgur.com/QzF08A1.png',
            fields=(
                {
                    'name': u'\U0001F54A'+' Tiempo de respuesta',
                    'value': f'Respondí en: {reply_time}ms.',
                    'inline': False
                },
                {
                    'name': u'\U0000270F'+' Tiempo de edición',
                    'value': f'Edité mi mensaje en: {edit_time}ms.',
                    'inline': False
                },
                {
                    'name': u'\U0001F4F0' + ' Tiempo total',
                    'value': (
                        'Entre tu mensaje y mi edición pasaron: '
                        f'{total_time}ms.'
                    ),
                    'inline': False
                }
            )
        )
        await pong_msg.edit(content='', embed=pong_embed)

    def get_milliseconds(self, time):
        """Toma un timedelta y devuelve los milisegundos."""
        return time.seconds*1000 + time.microseconds/1000


def setup(bot):
    bot.add_cog(Utility(bot))
