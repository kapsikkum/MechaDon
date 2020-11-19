# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 14:22:03
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-11-20 00:31:08
import asyncio
import io
import os
import time
import urllib.parse
from datetime import datetime, timedelta
from fractions import Fraction

import aiohttp
import discord
import html2text
import ujson as json
from discord.ext import commands
from disputils import BotConfirmation, BotEmbedPaginator

import core
import core.exceptions
import core.utils


class Advanced_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        description="Create a temporary server that gets deleted in 30 minutes.",
        usage="{prefix}tempserver create (To create a temporary server.)\n{prefix}tempserver delete (To delete a temporary server now.)",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def tempserver(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                embed=discord.Embed(
                    title="Invalid sub command given.",
                    description=f"Type {core.utils.prefix_for(ctx.message.guild)}help tempserver for help.",
                    color=0xFF0000,
                )
            )

    @tempserver.command(name="create")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    async def _create(self, ctx):
        check = core.tempserver_owners.get(ctx.message.author.id, None)
        if ctx.message.guild.owner.id == self.bot.user.id:
            await ctx.send(
                embed=discord.Embed(
                    title="Yeah no", description="Not happening.", color=0xFF0000
                )
            )
        elif check is not None:
            server = self.bot.get_guild(int(check))
            for channel in server.text_channels:
                inv = await channel.create_invite()
                break
            await ctx.send(
                embed=discord.Embed(
                    title="Yeah no",
                    description=f"Not happening.\nYou've already made a tempserver called {server.name}.\n{inv.url}",
                    color=0xFF0000,
                )
            )
        else:
            m = await ctx.send(
                embed=discord.Embed(
                    title="Please Wait...",
                    description="Creating server...",
                    color=0xFF0000,
                )
            )
            server = await self.bot.create_guild(
                name=core.utils.create_random_word_string()
            )
            await asyncio.sleep(3)
            server = self.bot.get_guild(server.id)
            await m.edit(
                embed=discord.Embed(
                    title="Please Wait...",
                    description="Setting up role permissions...",
                    color=0xFF0000,
                )
            )
            await server.default_role.edit(permissions=discord.Permissions.all())
            await m.edit(
                embed=discord.Embed(
                    title="Please Wait...",
                    description="Setting up channels...",
                    color=0xFF0000,
                )
            )
            for channel in server.channels:
                await channel.delete()
            await server.create_text_channel("general")
            await server.create_voice_channel("General")
            for channel in server.text_channels:
                inv = await channel.create_invite()
                await m.edit(
                    embed=discord.Embed(
                        title="Done. Here is the invite.",
                        description=inv.url,
                        color=0xFF0000,
                    )
                )
                break
            core.tempserver_owners[ctx.message.author.id] = server.id
            self.bot.loop.create_task(
                core.utils.server_deletion(server, ctx.message.author.id)
            )

    @tempserver.command(name="delete")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def _delete(self, ctx):
        check = core.tempserver_owners.get(ctx.message.author.id, None)
        if check is not None:
            server = self.bot.get_guild(int(check))
            if server.owner.id == self.bot.user.id:
                await server.delete()
                if ctx.message.guild.owner.id != self.bot.user.id:
                    await ctx.send(
                        embed=discord.Embed(
                            title=f"Deleted the tempserver: {server.name}",
                            description=discord.Embed.Empty,
                            color=0xFF0000,
                        )
                    )
            del core.tempserver_owners[ctx.message.author.id]
        else:
            if ctx.message.guild.owner.id == self.bot.user.id:
                await ctx.send(
                    embed=discord.Embed(
                        title="This is not your tempserver.",
                        description="Ask the person who made it to delete it.",
                        color=0xFF0000,
                    )
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="You haven't made a tempserver.",
                        description=f"Type {core.utils.prefix_for(ctx.message.guild)}help tempserver for help on creating one.",
                        color=0xFF0000,
                    )
                )

    @commands.command(
        description="Make the last deleted message in the channel not deleted anymore."
    )
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def undelete(self, ctx, amount: int = 1):
        if not str(ctx.message.channel.id) in core.deletions:
            raise core.exceptions.CommandError("Nothing was deleted here.")
        elif len(core.deletions[str(ctx.message.channel.id)]) == 0:
            raise core.exceptions.CommandError("Nothing was deleted here.")
        else:
            messages = list(reversed(core.deletions[str(ctx.message.channel.id)]))
            for x in range(0, amount):
                try:
                    message = messages[x]
                except:
                    pass
                else:
                    if len(message.content) != 0:
                        embed = discord.Embed(
                            title=discord.Embed.Empty,
                            description=message.content,
                            color=0xFF0000,
                            timestamp=message.created_at,
                        )
                        embed.set_footer(
                            text=message.author.name, icon_url=message.author.avatar_url
                        )
                        await ctx.send(embed=embed)

                    for embed in message.embeds:
                        embed.set_footer(
                            text=message.author.name, icon_url=message.author.avatar_url
                        )
                        await ctx.send(embed=embed)

                    for attachment in message.attachments:
                        filetype = os.path.splitext(attachment.url)[1]
                        if filetype in [".png", ".webp", ".jpg", ".jpeg", ".gif"]:
                            embed = discord.Embed(
                                title="Deleted Image",
                                description=discord.Embed.Empty,
                                color=0xFF0000,
                                timestamp=message.created_at,
                            )
                            embed.set_image(
                                url=attachment.url.replace(
                                    "cdn.discordapp.com", "media.discordapp.net"
                                )
                            )
                            embed.set_footer(
                                text=message.author.name,
                                icon_url=message.author.avatar_url,
                            )
                            await ctx.send(embed=embed)

                        elif filetype in [".webm", ".mp4", ".mov"]:
                            embed = discord.Embed(
                                title="Deleted Video",
                                description=discord.Embed.Empty,
                                color=0xFF0000,
                                timestamp=message.created_at,
                            )
                            embed.set_footer(
                                text=message.author.name,
                                icon_url=message.author.avatar_url,
                            )
                            await ctx.send(
                                attachment.url.replace(
                                    "cdn.discordapp.com", "media.discordapp.net"
                                ),
                                embed=embed,
                            )

                        else:
                            await ctx.send(
                                attachment.url.replace(
                                    "cdn.discordapp.com", "media.discordapp.net"
                                ),
                            )

                    try:
                        core.deletions[str(ctx.message.channel.id)].remove(message)
                    except:
                        pass

    @commands.command(hidden=True, description="Make Messages never get deleted.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    # @commands.is_owner()
    @commands.has_permissions(administrator=True)
    async def nodelete(self, ctx, all=None):
        if all == "all":
            on = 0
            off = 0
            for channel in ctx.guild.text_channels:
                if str(channel.id) in core.nodelete_chans:
                    core.nodelete_chans.remove(str(channel.id))
                    off += 1
                else:
                    core.nodelete_chans.append(str(channel.id))
                    on += 1
            await ctx.send(
                embed=discord.Embed(
                    title=f"No-Delete Turned on for {on} channels and off for {off} channels.",
                    description=discord.Embed.Empty,
                    color=0xFF0000,
                )
            )
        else:
            if str(ctx.channel.id) in core.nodelete_chans:
                core.nodelete_chans.remove(str(ctx.channel.id))
                await ctx.send(
                    embed=discord.Embed(
                        title="No-Delete Turned off for this channel.",
                        description=discord.Embed.Empty,
                        color=0xFF0000,
                    )
                )
            else:
                core.nodelete_chans.append(str(ctx.channel.id))
                await ctx.send(
                    embed=discord.Embed(
                        title="No-Delete Turned on for this channel.",
                        description=discord.Embed.Empty,
                        color=0xFF0000,
                    )
                )

    @commands.command(
        description="Get Human to bot Ratio.", aliases=["htb", "h:b", "human:bot"]
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    async def humantobot(self, ctx):
        members = {"humans": 0, "bots": 0}
        for member in ctx.guild.members:
            if member.bot:
                members["bots"] += 1
            else:
                members["humans"] += 1
        await ctx.send(
            embed=discord.Embed(
                title="Human:bot ratio",
                description=f"{members['humans']}:{members['bots']}",
                color=0xFF0000,
            )
        )

    @commands.command(
        description="Convert HTML to Markdown.",
        usage="{prefix}html <html code or html in file attached>",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def html(self, ctx, *, code=None):
        if len(ctx.message.attachments) == 0:
            if code is not None:
                markdown = html2text.html2text(code)
                for partition in [
                    markdown[i : i + 2000] for i in range(0, len(markdown), 2000)
                ]:
                    await ctx.send(
                        embed=discord.Embed(
                            title=discord.Embed.Empty,
                            description=partition,
                            color=0xFF0000,
                        )
                    )
            else:
                raise core.exceptions.CommandError("No HTML given.")
        else:
            attachment = ctx.message.attachments[0].url
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment) as r:
                    if r.status == 200:
                        markdown = html2text.html2text(await r.text())
                        for partition in [
                            markdown[i : i + 2000]
                            for i in range(0, len(markdown), 2000)
                        ]:
                            await ctx.send(
                                embed=discord.Embed(
                                    title=discord.Embed.Empty,
                                    description=partition,
                                    color=0xFF0000,
                                )
                            )

    @commands.command(
        description="Translate a message.",
        usage="{prefix}translate --from/-f <optional (default auto-detect)> --to/-t <optional (default english)> <text to translate>\n Type `{prefix}langs` for all supported languages.",
        aliases=["tr"],
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def translate(self, ctx, *, text):
        data = core.utils.check_flags("".join(text))
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://www.bing.com/ttranslatev3",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data=f'fromLang={data["from"]}&text={urllib.parse.quote(data["text"])}&to={data["to"]}',
                ) as result:
                    if result.status == 200:
                        result = await result.json()
                        try:
                            result["StatusCode"]
                        except:
                            pass
                        else:
                            raise core.exceptions.CommandError(
                                f"Bing API error code {result['StatusCode']}"
                            )
                        await ctx.send(
                            embed=discord.Embed(
                                title=f"""Translated `{(core.langs.get(data["from"], f"Unknown Language ({data['from']})") if data["from"] != "auto-detect" else core.langs.get(result[0]['detectedLanguage']['language'], f"Unknown Language ({result[0]['detectedLanguage']['language']})"))}` -> `{core.langs.get(data["to"], f"Unknown Language ({data['to']})")}`""",
                                description=result[0]["translations"][0]["text"],
                                color=0xFF0000,
                            )
                        )
                    else:
                        raise core.exceptions.CommandError(
                            f"Bing API error code {result.status}"
                        )

    @commands.command(description="Translate a message.", name="langs", hidden=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def lan(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Supported Translate Languages",
                description=",\n".join(f"{core.langs[l]} (`{l}`)" for l in core.langs),
                color=0xFF0000,
            )
        )

    @commands.group(
        description="Create a public tag.",
        usage="{prefix}tag add|remove|edit|owner|tag to view",
        aliases=["t", "tags"],
        invoke_without_command=True,
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def tag(self, ctx, tag=None):
        if tag is None:
            raise core.exceptions.CommandError("No Command or tag given.")
        tag_content = await core.utils.get_tag(tag)
        await ctx.send(
            tag_content.replace("@everyone", "@nobody")
            .replace("@here", "@there")
            .format(user=ctx.author)
        )

    @tag.command()
    @commands.cooldown(2, 3, commands.BucketType.user)
    async def add(self, ctx, tag=None, *, string=None):
        if tag is None:
            raise core.exceptions.CommandError("You did not specify a tag!")
        if string is None:
            raise core.exceptions.CommandError("You did not specify any content!")
        await core.utils.add_tag(tag, string, ctx.author.id)
        await ctx.send(
            embed=discord.Embed(
                title=discord.Embed.Empty,
                description=f'Added tag **"{tag}"**.',
                color=0xFF0000,
            )
        )

    @tag.command()
    @commands.cooldown(2, 3, commands.BucketType.user)
    async def remove(self, ctx, tag=None):
        if tag is None:
            raise core.exceptions.CommandError("You did not specify a tag!")
        await core.utils.remove_tag(tag, ctx.author.id)
        await ctx.send(
            embed=discord.Embed(
                title=discord.Embed.Empty,
                description=f'Removed tag **"{tag}"**.',
                color=0xFF0000,
            )
        )

    @tag.command()
    @commands.cooldown(2, 3, commands.BucketType.user)
    async def edit(self, ctx, tag=None, *, string=None):
        if tag is None:
            raise core.exceptions.CommandError("You did not specify a tag!")
        if string is None:
            raise core.exceptions.CommandError("You did not specify any content!")
        await core.utils.edit_tag(tag, string, ctx.author.id)
        await ctx.send(
            embed=discord.Embed(
                title=discord.Embed.Empty,
                description=f'Edited tag **"{tag}"**.',
                color=0xFF0000,
            )
        )

    @tag.command()
    @commands.cooldown(2, 3, commands.BucketType.user)
    async def owner(self, ctx, tag=None):
        if tag is None:
            raise core.exceptions.CommandError("You did not specify a tag!")
        user = await self.bot.fetch_user(await core.utils.get_tag_owner(tag))
        await ctx.send(
            embed=discord.Embed(
                title=discord.Embed.Empty,
                description=f"Owner: {user.name}#{user.discriminator} ({user.id})",
                color=0xFF0000,
            )
        )

    @tag.command(name="list")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _list(self, ctx, user: discord.User = None):
        if user is None:
            user = ctx.author
        embeds = list()
        string = str()
        count = 0
        tags = await core.utils.list_user_tags(user.id)
        if len(tags) == 0:
            if user.id == ctx.author.id:
                raise core.exceptions.CommandError("You do not own any tags!")
            else:
                raise core.exceptions.CommandError("They do not own any tags!")
        for tag in tags:
            string += f"""{tags.index(tag) + 1}. **"{tag[0][:35]}{("..." if len(tag[0][:35]) < len(tag[0]) else "")}"**\n"""
            count += 1
            if count == 20:
                embeds.append(
                    discord.Embed(
                        title=f"Tags for {user.name}",
                        description=string,
                        color=0xFF0000,
                    )
                )
                count = 0
                string = str()
        if count > 0:
            embeds.append(
                discord.Embed(
                    title=f"Tags for {user.name}", description=string, color=0xFF0000
                )
            )
            count = 0
            string = str()

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.guild_only()
    async def massnick(self, ctx, *, nickname=None):
        if nickname is None:
            self.massnick.reset_cooldown(ctx)
            raise core.exceptions.CommandError("No nickname or subcommand was given.")

        confirmation = BotConfirmation(ctx, 0xFF0000)
        await confirmation.confirm("Are you sure?")

        if confirmation.confirmed:
            await ctx.send(
                embed=discord.Embed(
                    title="Alright.",
                    description="This may take a while",
                    color=0xFF0000,
                )
            )
            success, failed = (0, 0)
            for member in ctx.guild.members:
                try:
                    await member.edit(nick=nickname[:32])
                    success += 1
                except:
                    failed += 1
            await ctx.send(
                embed=discord.Embed(
                    title="Finished",
                    description=f"""Successfully renamed **{success}** member(s){(f", failed to rename **{failed}** member(s) due to permissions or having a role higher than me." if failed > 0 else ".")}""",
                    color=0xFF0000,
                )
            )
        else:
            self.massnick.reset_cooldown(ctx)

    @massnick.command()
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.guild_only()
    async def reset(self, ctx):
        confirmation = BotConfirmation(ctx, 0xFF0000)
        await confirmation.confirm("Are you sure?")

        if confirmation.confirmed:
            await ctx.send(
                embed=discord.Embed(
                    title="Alright.",
                    description="This may take a while",
                    color=0xFF0000,
                )
            )
            success, failed = (0, 0)
            for member in ctx.guild.members:
                try:
                    await member.edit(nick=None)
                    success += 1
                except:
                    failed += 1
            await ctx.send(
                embed=discord.Embed(
                    title="Finished",
                    description=f"""Successfully reset **{success}** member(s){(f", failed to reset **{failed}** member(s) due to permissions or having a role higher than me." if failed > 0 else ".")}""",
                    color=0xFF0000,
                )
            )
        else:
            self.reset.reset_cooldown(ctx)
