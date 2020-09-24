from discord.ext.commands import check, Context


def is_listing():
    async def predicate(ctx: Context):
        params = ctx.message.content.split(' ')
        return len(params) == 1 or params[1] == 'check'
    return check(predicate)


async def is_enabled(ctx: Context):
    async def get_disabled_from_db(bot, guild):
        settings = await bot.get_cog('Settings').get_or_create_guild_settings(guild)
        disabled_cogs = settings.disabled_cogs or []
        disabled_commands = settings.disabled_commands or []
        ctx.bot.cache.set_list('disabled_cogs', guild.id, disabled_cogs)
        ctx.bot.cache.set_list('disabled_commands', guild.id, disabled_commands)
        return disabled_cogs, disabled_commands

    guild = ctx.message.guild
    if guild:
        # pylint: disable=protected-access
        disabled_cogs = ctx.bot.cache.get('disabled_cogs', guild.id)
        disabled_commands = ctx.bot.cache.get_list('disabled_commands', guild.id)
        if disabled_cogs is None or disabled_commands is None:
            disabled_cogs, disabled_commands = await get_disabled_from_db(ctx.bot, guild)
        is_settings = ctx.cog.qualified_name == 'Settings' if ctx.cog else False
        is_cog_disabled = ctx.cog.qualified_name in disabled_cogs if ctx.cog else False
        is_command_disabled = ctx.command.name in disabled_commands
        return is_settings or not (is_cog_disabled or is_command_disabled)
    return True


def can_change_nickname():
    async def predicate(ctx: Context):
        mentions = ctx.message.mentions
        author = ctx.message.author
        is_changing_own = len(mentions) == 1 and author in mentions
        return is_changing_own and author.guild_permissions.change_nickname
    return check(predicate)
