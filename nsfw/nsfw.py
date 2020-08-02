import asyncio
import random

import aiohttp
import discord
from discord.ext import commands

import core
import core.exceptions
import core.utils
from nsfw import (danbooru, e621, gelbooru, hypnohub, konachan, realbooru,
                  rule34, xbooru, yandere)


class NSFW_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.danbooru = danbooru.DanbooruClient(bot)
        self.gelbooru = gelbooru.GelbooruClient(bot)
        self.konachan = konachan.KonaChanClient(bot)
        self.realbooru = realbooru.RealbooruClient(bot)
        self.rule34 = rule34.Rule34Client(bot)
        self.xbooru = xbooru.XbooruClient(bot)
        self.yandere = yandere.YandereClient(bot)
        self.hypnohub = hypnohub.HypnoHubClient(bot)
        self.e621 = e621.e621Client(bot)
    
    @commands.command(description="Get a random image from a specified tag from DanBooru. (NSFW)", usage="{prefix}danbooru <tags>", name="danbooru")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def danbooru_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts= await self.danbooru.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from GelBooru. (NSFW)", usage="{prefix}gelbooru <tags>", name="gelbooru")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def gelbooru_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.gelbooru.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from KonaChan. (NSFW)", usage="{prefix}konachan <tags>", name="konachan")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def konachan_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.konachan.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from RealBooru. (NSFW)", usage="{prefix}realbooru <tags>", name="realbooru")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def realbooru_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.realbooru.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from Rule34. (NSFW)", usage="{prefix}rule34 <tags>", name="rule34", aliases=['r34'])
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def rule34_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts= await self.rule34.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from XBooru. (NSFW)", usage="{prefix}xbooru <tags>", name="xbooru")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def xbooru_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.xbooru.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from Yande.re. (NSFW)", usage="{prefix}yandere <tags>", name="yandere")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def yandere_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.yandere.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from HypnoHub. (NSFW, Hypno fetish site)", usage="{prefix}hypnohub <tags>", name="hypnohub")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def hypnohub_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.hypnohub.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)

    @commands.command(description="Get a random image from a specified tag from e621. (NSFW, Furry fetish site)", usage="{prefix}e621 <tags>", name="e621")
    @commands.is_nsfw()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def e621_(self, ctx, *, tag=""):
        async with ctx.typing():
            posts = await self.e621.get_images(tag)
            if len(posts) == 0:
                embed = discord.Embed(title="No Results.", description=discord.Embed.Empty, color=0xff0000)
            else:
                post = random.choice(posts)
                embed = discord.Embed(title=(tag if len(tag) > 0 else 'Recent Image'), description=f"[Source]({post['post_url']})", color=0xff0000)
                embed.set_image(url=post['file_url'])
        await ctx.send(embed=embed)
