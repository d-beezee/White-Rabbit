import asyncio

import lightbulb
from lightbulb import commands, converters
import hikari
from hikari import permissions

from utils.localization import LOCALIZATION_DATA
from utils import gamedata, constants

plugin = lightbulb.Plugin("Admin")
plugin.add_checks(lightbulb.has_guild_permissions(permissions.Permissions.ADMINISTRATOR))
loc = LOCALIZATION_DATA["commands"]["admin"]
GROUP_CHAT = LOCALIZATION_DATA["channels"]["texts"]["group-chat"]


@plugin.command()
@lightbulb.command(loc["show_all"]["name"], loc["show_all"]["description"], aliases=loc["show_all"]["aliases"])
@lightbulb.implements(lightbulb.PrefixCommand)
async def show_all(ctx: lightbulb.Context) -> None:
    for channel in ctx.get_guild().get_channels():
        if channel.type != hikari.ChannelType.GUILD_TEXT or not channel.parent_id:
            continue
        parent = ctx.get_guild().get_channel(channel.parent_id)
        await channel.edit(permission_overwrites=parent.permission_overwrites.values())

@plugin.command()
@lightbulb.option("text_channels", "channels to wipe", modifier=commands.OptionModifier.GREEDY)
@lightbulb.command(loc["wipe"]["name"], loc["wipe"]["description"], aliases=loc["wipe"]["aliases"])
@lightbulb.implements(lightbulb.PrefixCommand)
async def wipe(ctx: lightbulb.Context) -> None:
    """Erases all messages and clears game data"""

    # Confirm command to user
    await ctx.respond(loc["wipe"]["DeletingMessages"])

    # Wipe messages
    if not text_channels:
        text_channels = ctx.guild.text_channels
    for text_channel in text_channels:
        asyncio.create_task(text_channel.purge(limit=None))

    # Reset game data
    ctx.game.__init__(ctx.game.guild)

    # Console logging
    print(f'{constants.INFO_PREFIX}Wiped messages from server: "{ctx.guild.name}" (ID: {ctx.guild.id})')

@plugin.command()
@lightbulb.command(loc["reset_perms"]["name"], loc["reset_perms"]["description"], aliases=loc["reset_perms"]["aliases"])
@lightbulb.implements(lightbulb.PrefixCommand)
async def reset_perms(ctx: lightbulb.Context) -> None:
    """Resets channel permissions to the default (undoes !show_all)"""

    everyone = ctx.guild.default_role
    spectator = ctx.game.spectator_role

    for channel in ctx.guild.text_channels:
        # Clues channels
        if channel.name in LOCALIZATION_DATA["channels"]["clues"].values():
            asyncio.create_task(channel.set_permissions(
                everyone,
                view_channel=False,
                send_messages=False
            ))
            asyncio.create_task(channel.set_permissions(spectator, view_channel=True))

            player = channel.name.split("-")[0].title()
            for role in ctx.get_guild().get_roles():
                if role.name == player:
                    asyncio.create_task(channel.set_permissions(role, view_channel=True))

        # Channels that all players can send messages
        elif channel.name in [GROUP_CHAT, LOCALIZATION_DATA["channels"]["voicemails"]]:
            asyncio.create_task(channel.set_permissions(everyone, send_messages=False))
            for role in ctx.get_guild().get_roles():
                if role.name.lower() in gamedata.CHARACTERS:
                    asyncio.create_task(channel.set_permissions(role, send_messages=True))

        # Private message channels
        elif channel.name in LOCALIZATION_DATA["channels"]["texts"].values() and channel.name != GROUP_CHAT:
            asyncio.create_task(channel.set_permissions(everyone, view_channel=False, send_messages=None))
            asyncio.create_task(channel.set_permissions(spectator, view_channel=True, send_messages=False))
            split_name = channel.name.split("-")
            player_a = split_name[0].title()
            player_b = split_name[1].title()
            for role in ctx.get_guild().get_roles():
                if role.name in [player_a, player_b]:
                    asyncio.create_task(channel.set_permissions(role, view_channel=True))

@plugin.command()
@lightbulb.command(loc["reset_roles"]["name"], loc["reset_roles"]["description"], aliases=loc["reset_roles"]["aliases"])
@lightbulb.implements(lightbulb.PrefixCommand)
async def reset_roles(ctx: lightbulb.Context) -> None:
    # Removes character roles from everyone
    for member in ctx.guild.members:
        is_player = False
        if not member.bot:
            for role in member.roles:
                if role.name.lower() in gamedata.CHARACTERS.keys():
                    await member.remove_roles(role)
                    is_player = True
            if is_player:
                if member is ctx.guild.owner:
                    await ctx.respond(loc["reset_roles"]["NoteAboutOwner"])
                else:
                    await member.edit(nick=None)

@plugin.command()
@lightbulb.command(loc["reset"]["name"], loc["reset"]["description"], aliases=loc["reset"]["aliases"])
@lightbulb.implements(lightbulb.PrefixCommand)
async def reset(ctx: lightbulb.Context) -> None:
    """Complete server reset"""

    # Confirm command to user
    await ctx.respond(loc["reset"]["ResettingServer"])

    # Console logging
    print(f'{constants.INFO_PREFIX}Resetting server: "{ctx.guild.name}" (ID: {ctx.guild.id})')

    # Erase all messages and reset channel permissions
    await asyncio.gather(wipe(ctx), reset_perms(ctx), reset_roles(ctx))




def load(bot):
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)