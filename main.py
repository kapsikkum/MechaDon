import asyncio
import datetime as dt
import json
import logging
import os
import sys
import time
import traceback

import aiohttp
import discord
import humanize
from discord.ext import commands

import core
import core.exceptions
import core.utils
from core import admin, advanced, audio, basic, currency, files
from nsfw import danbooru, nsfw


def get_prefix(bot, message):
    prefixes = core.server_prefixes()
    if message.guild is None:
        return commands.when_mentioned_or(core.prefix)(bot, message)
    elif str(message.guild.id) in prefixes:
        return commands.when_mentioned_or(prefixes[str(message.guild.id)])(bot, message)
    else:
        return commands.when_mentioned_or(core.prefix)(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, help_command=None)


@bot.event
async def on_ready():
    if not core.started:
        await bot.change_presence(activity=discord.Activity(name='and Looking 👀', type=discord.ActivityType.watching))
        core.started = True
        core.logger.info("Changed Status.")
    botinfo = await bot.application_info()
    core.owner_id = botinfo.owner.id
    core.logger.info(f"Hello, {botinfo.owner.name}!")
    core.logger.info("Checking Database")
    await core.utils.check_db()
    if not "general" in list(await core.utils.shop_catalog()):
        await core.utils.shop_catalog(catalog="general", nsfw=False, content={"Burger": {"name": "Burger","type": "text","product": "\ud83c\udf54","price": 5.6,"quantity": 25,"permanent": False,"nsfw": False}}, mode="c")
    core.logger.info("Checking Servers")
    async for guild in bot.fetch_guilds(limit=None):
        guild = bot.get_guild(guild.id)
        ids = list()
        for member in guild.members:
            ids.append(member.id)
        if not core.owner_id in ids:
            core.logger.info(f"Leaving: {guild.name} Due to you not being there.")
            if guild.owner.id == bot.user.id:
                await guild.delete()
            else:
                await guild.leave()
    core.logger.info("Ready.")
    core.logger.info(f"Bot Version: {core.__version__}")
    core.logger.info(f"Logged in as {bot.user.name}#{bot.user.discriminator}.")
    core.logger.info(f"Member of {len(bot.guilds)} Guild(s).")
    core.logger.info(f"Default Prefix: {core.prefix}")


@bot.event
async def on_command_error(ctx, e):
    core.logger.error(str(e))
    core.logger.debug(''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))
    try:
        e.original
    except:
        if isinstance(e, commands.CommandNotFound):
            await ctx.message.add_reaction("⁉")
        elif isinstance(e, commands.CommandOnCooldown):
            await ctx.send(embed=discord.Embed(title="You're on Cooldown!",  description=f"Try again in **{humanize.naturaldelta(e.retry_after)}**", color=0xff0000))
        elif isinstance(e, commands.NSFWChannelRequired):
            await ctx.send(embed=discord.Embed(title="This channel is not marked as NSFW",  description="Do this command in a NSFW channel or DMs.", color=0xff0000))
        else:
            if core.debug_mode:
                await ctx.send(embed=discord.Embed(title="Error:",  description='```{error}```'.format(error=''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)), color=0xff0000)))
            else:
                await ctx.send(embed=discord.Embed(title="Error:",  description=str(e), color=0xff0000))
    else:
        if isinstance(e.original, core.exceptions.CommandError):
            await ctx.send(embed=discord.Embed(title="Error:",  description=str(e.original), color=0xff0000))
        else:
            await core.utils.report_exception(e.original)
            if core.debug_mode:
                await ctx.send(embed=discord.Embed(title="Error:",  description='```{error}```'.format(error=''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)), color=0xff0000)))
            else:
                await ctx.send(embed=discord.Embed(title="Error:",  description=str(e), color=0xff0000))


@bot.event
async def on_guild_join(guild):
    ids = list()
    for member in guild.members:
        ids.append(member.id)
    if not core.owner_id in ids:
        try:
            await guild.leave()
        except:
            pass


@bot.event
async def on_message(message):
    core.messages.put_nowait(message)
    try:
        core.censor_check[str(message.guild.id)]
    except:
        pass
    else:
        if str(message.author.id) in core.censor_check[str(message.guild.id)]:
            if str(message.author.id) == str(bot.user.id):
                await bot.process_commands(message)
            elif str(message.author.id) == str(core.owner_id):
                await bot.process_commands(message)
            else:
                try:
                    await message.delete()
                except:
                    pass
                return
    await bot.process_commands(message)
    if not message.author.bot:
        try:
            core.user_currency[str(message.author.id)]
        except:
            core.user_currency[str(message.author.id)] = 0.02
        else:
            core.user_currency[str(message.author.id)] += 0.02
            with open("core/bonus.json", mode="w") as f:
                json.dump(core.user_currency, f, indent=4)
    if not message.author.id == bot.user.id and not message.author.bot:
        if "@someone" in message.content:
            await message.channel.send(f"i gotchu, {core.utils.random.choice(message.guild.members).mention}")
        if "SAD!" in message.content:
            await message.add_reaction("😔")
        if "desu wa" in message.content.lower():
            for char in ['🇩', '🇪', '🇸', '🇺', '<:desuwa:680754352356327433>', '🇼', '🇦']:
                await message.add_reaction(char)
        if message.content.startswith("cum"):
            await message.add_reaction("™")


@bot.event
async def on_message_delete(message):
    if str(message.channel.id) in core.nodelete_chans:
        if message.author.id != 700328866962604112: # poop bot don't like
            try:
                webhooks = await message.channel.webhooks()
                if len(webhooks) == 0:
                    webhook = await message.channel.create_webhook(name=bot.user.name, reason='No Delete.')
                else:
                    webhook = webhooks[0]
                webhook = webhook.url
                await core.utils.revive_message(message, webhook)
            except Exception:
                pass
    else:
        try:
            core.deletions[str(message.channel.id)]
        except:
            core.deletions[str(message.channel.id)] = core.utils.ExpireList()
        core.deletions[str(message.channel.id)].append(message)

        if len(message.mentions) > 0:
            time = dt.datetime.utcnow() - message.created_at
            if time.seconds < 10:
                await message.channel.send(embed=discord.Embed(title="Ghost ping detected!", description=f"{message.author.mention} ghost pinged {', '.join(map(core.utils.get_mention, message.mentions))}", color=0xff0000))


@bot.event
async def on_raw_bulk_message_delete(event):
    for message in event.cached_messages:
        if message.author.id != 700328866962604112: # gay farisbot :)
            try:
                webhooks = await message.channel.webhooks()
                if len(webhooks) == 0:
                    webhook = await message.channel.create_webhook(reason='No Delete.')
                else:
                    webhook = webhooks[0]
                webhook = webhook.url
                await core.utils.revive_message(message, webhook)
            except:
                pass
    else:
        try:
            core.deletions[str(event.channel_id)]
        except:
            core.deletions[str(event.channel_id)] = core.utils.ExpireList()
        core.deletions[str(event.channel_id)].append(message)


@bot.event
async def on_message_edit(before, after):
    if str(after.channel.id) in core.nodelete_chans:
        if after.flags.value == 4:
            await after.edit(flags=0)


bot.add_cog(basic.Basic_Commands(bot))
bot.add_cog(advanced.Advanced_Commands(bot))
bot.add_cog(currency.Currency_Commands(bot))
bot.add_cog(admin.Admin_Commands(bot))
bot.add_cog(files.File_Commands(bot))
bot.add_cog(audio.Audio_Commands(bot))
bot.add_cog(nsfw.NSFW_Commands(bot))
# bot.loop.create_task(core.utils.message_logger())
bot.run(core.token)
