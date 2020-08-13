# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 14:22:38
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-13 14:22:38
import ast
import asyncio
import io
import re
import sys
import time
import traceback
from datetime import datetime, timedelta

import aiohttp
import discord
from discord.ext import commands

import core
import core.exceptions
import core.utils


def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Admin_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status = discord.Status.online
        self.activity = discord.Activity(
            name="and Looking 👀", type=discord.ActivityType.watching
        )

    @commands.command(
        description="Change the bots prefix in this server. (Admin Only)",
        usage="{prefix}prefix set <prefix> | {prefix}prefix reset",
    )
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, mode=None, prefix=None):
        if mode is not None:
            if mode == "reset":
                core.server_prefixes(
                    id=ctx.message.guild.id, prefix=core.prefix, mode="w"
                )
                await ctx.send(
                    embed=discord.Embed(
                        title=f"Prefix Reset.",
                        description=f"New Prefix is: {core.prefix}",
                        color=0xFF0000,
                    )
                )
            elif mode == "set":
                if prefix is not None:
                    core.server_prefixes(
                        id=ctx.message.guild.id, prefix=prefix, mode="w"
                    )
                    await ctx.send(
                        embed=discord.Embed(
                            title=f"Prefix Changed.",
                            description=f"New Prefix is: {prefix}",
                            color=0xFF0000,
                        )
                    )

    @commands.command(
        description="Stop a user from talking. (Admin Only)",
        usage="{prefix}censor <user or users>",
    )
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def censor(self, ctx, *, users):
        try:
            core.censor_check[str(ctx.message.guild.id)]
        except:
            core.censor_check[str(ctx.message.guild.id)] = list()
        for user in map(
            lambda user: self.bot.get_user(int(user.group(0))),
            re.finditer("[0-9]{18}", users),
        ):
            if user.id == core.owner_id or user.id == self.bot.user.id:
                if ctx.author.id == core.owner_id:
                    if str(user.id) in core.censor_check[str(ctx.message.guild.id)]:
                        core.censor_check[str(ctx.message.guild.id)].remove(
                            str(user.id)
                        )
                        await ctx.send(
                            embed=discord.Embed(
                                title="Ok done.",
                                description=f"No longer censoring {user.mention}.",
                                color=0xFF0000,
                            )
                        )
                    else:
                        await ctx.send(
                            embed=discord.Embed(
                                title="Nah.",
                                description=discord.Embed.Empty,
                                color=0xFF0000,
                            )
                        )
                        return
                user = ctx.author
            if str(user.id) in core.censor_check[str(ctx.message.guild.id)]:
                core.censor_check[str(ctx.message.guild.id)].remove(str(user.id))
                await ctx.send(
                    embed=discord.Embed(
                        title="Ok done.",
                        description=f"No longer censoring {user.mention}.",
                        color=0xFF0000,
                    )
                )
            else:
                core.censor_check[str(ctx.message.guild.id)].append(str(user.id))
                await ctx.send(
                    embed=discord.Embed(
                        title="Ok done.",
                        description=f"Censoring {user.mention}.",
                        color=0xFF0000,
                    )
                )

    @commands.command(
        description="Clears the specified amount of messages in a channel.",
        usage="{prefix}clear <amount>",
        hidden=True,
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clear(self, ctx, limit: int):
        try:
            await ctx.channel.purge(limit=limit + 1)
        except:
            pass
        m = await ctx.send(
            embed=discord.Embed(
                title=f"Finished Clearing {limit} messages",
                description="",
                color=0xFF0000,
            )
        )
        await asyncio.sleep(10)
        await m.delete()

    @commands.command(
        description="Kick a user. (Admin Only)",
        usage="{prefix}kick @user <optional reason>",
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def kick(self, ctx, member: discord.Member = None, *, reason=None):
        if member.id == self.bot.user.id:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Goodbye, {member.name}",
                    description="Just kidding i'm not kicking myself dumbass.",
                    color=0xFF0000,
                )
            )
        else:
            await member.kick(reason=reason)
            await ctx.send(
                embed=discord.Embed(
                    title=f"Goodbye, {member.name}",
                    description=discord.Embed.Empty,
                    color=0xFF0000,
                )
            )

    @commands.command(
        description="Ban a user. (Admin Only)",
        usage="{prefix}ban @user <optional reason>",
    )
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ban(self, ctx, member: discord.Member = None, *, reason=None):
        if member.id == self.bot.user.id:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Goodbye, {member.name}",
                    description="Just kidding i'm not banning myself dumbass.",
                    color=0xFF0000,
                )
            )
        else:
            await member.ban(reason=reason)
            await ctx.send(
                embed=discord.Embed(
                    title=f"Goodbye, {member.name}",
                    description="Don't come back.",
                    color=0xFF0000,
                )
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Ok chief.", description=discord.Embed.Empty, color=0xFF0000
            )
        )
        await self.bot.close()
        sys.exit()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, *, code):
        fn_name = "_eval_expr"
        code = code.strip("```")
        code = "\n".join(f"    {i}" for i in code.splitlines())
        body = f"async def {fn_name}():\n{code}"
        parsed = ast.parse(body)
        body = parsed.body[0].body
        insert_returns(body)
        env = {
            "bot": ctx.bot,
            "discord": discord,
            "commands": commands,
            "ctx": ctx,
            "__import__": __import__,
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        try:
            result = await eval(f"{fn_name}()", env)
        except Exception as e:
            result = "".join(
                traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            )
        await ctx.send(
            embed=discord.Embed(
                title="Eval Result:", description=f"```{result}```", color=0xFF0000
            )
        )

    @commands.group(hidden=True)
    @commands.is_owner()
    async def status(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                embed=discord.Embed(
                    title="Invalid command given.",
                    description=discord.Embed.Empty,
                    color=0xFF0000,
                )
            )

    @status.command(hidden=True, name="playing")
    @commands.is_owner()
    async def _playing(self, ctx, *, status):
        self.activity = discord.Activity(name=status, type=discord.ActivityType.playing)
        await self.bot.change_presence(status=self.status, activity=self.activity)

    @status.command(hidden=True, name="listening")
    @commands.is_owner()
    async def _listening(self, ctx, *, status):
        self.activity = discord.Activity(
            name=status, type=discord.ActivityType.listening
        )
        await self.bot.change_presence(status=self.status, activity=self.activity)

    @status.command(hidden=True, name="watching")
    @commands.is_owner()
    async def _watching(self, ctx, *, status):
        self.activity = discord.Activity(
            name=status, type=discord.ActivityType.watching
        )
        await self.bot.change_presence(status=self.status, activity=self.activity)

    @status.command(hidden=True, name="streaming")
    @commands.is_owner()
    async def _streaming(self, ctx, *, status):
        self.activity = discord.Activity(
            name=status,
            url="https://twitch.tv/blakeando1k",
            type=discord.ActivityType.streaming,
        )
        await self.bot.change_presence(status=self.status, activity=self.activity)

    @status.command(hidden=True, name="online")
    @commands.is_owner()
    async def _online(self, ctx):
        self.status = discord.Status.online
        await self.bot.change_presence(
            status=discord.Status.online, activity=self.activity
        )

    @status.command(hidden=True, name="idle")
    @commands.is_owner()
    async def _idle(self, ctx):
        self.status = discord.Status.idle
        await self.bot.change_presence(
            status=discord.Status.idle, activity=self.activity
        )

    @status.command(hidden=True, name="dnd")
    @commands.is_owner()
    async def _dnd(self, ctx):
        self.status = discord.Status.dnd
        await self.bot.change_presence(
            status=discord.Status.dnd, activity=self.activity
        )

    @status.command(hidden=True, name="offline")
    @commands.is_owner()
    async def _offline(self, ctx):
        self.status = discord.Status.offline
        await self.bot.change_presence(
            status=discord.Status.offline, activity=self.activity
        )

