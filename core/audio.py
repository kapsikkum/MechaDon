import asyncio
import io
import itertools
import os
import re
import sys
import tempfile
import traceback
from functools import partial

import aiofiles
import aiohttp
import discord
from async_timeout import timeout
from discord.ext import commands
from youtube_dl import YoutubeDL

import core
import core.exceptions
import core.utils

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'cache/youtube/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'continuedl': True
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.thumbnail = data.get('thumbnail')
        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        embed = discord.Embed(title=f'Added {data["title"]} to the Queue.',  description=discord.Embed.Empty, color=0xff0000)
        embed.set_image(url=data['thumbnail'])
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 'thumbnail': data['thumbnail']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info,
                         url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog',
                 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(embed=discord.Embed(title=f'There was an error processing your song.',  description=str(e), color=0xff0000))
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(
                source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            embed = discord.Embed(title=f'Now Playing:',  description=f'**{source.title}**\nRequested by `{source.requester}`', color=0xff0000)
            embed.set_thumbnail(url=source.thumbnail)
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))



class Audio_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    __slots__ = ('bot', 'players')

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connect', aliases=['join'], description="Connect to a voice channel.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise core.exceptions.CommandError('No channel to join. Please either specify a valid channel or join one.')
        vc = ctx.voice_client
        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise core.exceptions.CommandError(f'Moving to channel: {channel} timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise core.exceptions.CommandError(f'Connecting to channel: {channel} timed out.')

        await ctx.send(embed=discord.Embed(title=f'Connected to: {channel}',  description=discord.Embed.Empty, color=0xff0000), delete_after=10)
    
    @commands.command(name='play', aliases=['p'], description="Play a song from YouTube.", usage="{prefix}play <song name or link>")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def play_(self, ctx, *, search: str):
        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if re.match(regex, search) is not None:
            if not re.match("(http[s]?:\/\/)?(www\.youtube\.com\/watch\?v=|youtu\.be\/)[A-Za-z0-9_-]{11}", search):
                raise core.exceptions.CommandError("Not supported.")
        async with ctx.typing():
            vc = ctx.voice_client
            if not vc:
                await ctx.invoke(self.connect_)
            player = self.get_player(ctx)
            source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=True)
        await player.queue.put(source)

    @commands.command(name='pause', description="Pause the currently playing song.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pause_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_playing():
            return await ctx.send(embed=discord.Embed(title='Nothing is Playing.',  description=discord.Embed.Empty, color=0xff0000))
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(embed=discord.Embed(title=f'{ctx.author} Paused the song!',  description=discord.Embed.Empty, color=0xff0000))

    @commands.command(name='resume', description="Resume the currently paused song.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def resume_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send(embed=discord.Embed(title='Nothing is Playing.',  description=discord.Embed.Empty, color=0xff0000))
        elif not vc.is_paused():
            return
        vc.resume()
        await ctx.send(embed=discord.Embed(title=f'{ctx.author} Resumed the song!',  description=discord.Embed.Empty, color=0xff0000))

    @commands.command(name='skip', aliases=['s'], description="Skip the currently playing song.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def skip_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send(embed=discord.Embed(title='Nothing is Playing.',  description=discord.Embed.Empty, color=0xff0000))
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        vc.stop()
        await ctx.send(embed=discord.Embed(title=f'{ctx.author} Skipped the song!',  description=discord.Embed.Empty, color=0xff0000))

    @commands.command(name='queue', aliases=['q', 'playlist'], description="Show the songs in the queue.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def queue_info(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send(embed=discord.Embed(title='Not connected to a voice channel.',  description=discord.Embed.Empty, color=0xff0000))
        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send(embed=discord.Embed(title='There are no more songs.',  description=discord.Embed.Empty, color=0xff0000))
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))
        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)}', description=fmt, color=0xff0000)

        await ctx.send(embed=embed)

    @commands.command(name='now_playing', aliases=['np', 'current', 'currentsong'], description="Display information about the currently playing song.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def now_playing_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send(embed=discord.Embed(title='Not connected to a voice channel.',  description=discord.Embed.Empty, color=0xff0000))
        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send(embed=discord.Embed(title='Nothing is Playing.',  description=discord.Embed.Empty, color=0xff0000))
        try:
            await player.np.delete()
        except discord.HTTPException:
            pass
        embed = discord.Embed(title=f'Now Playing:',  description=f'**{vc.source.title}**\nRequested by `{vc.source.requester}`', color=0xff0000)
        embed.set_thumbnail(url=vc.source.thumbnail)
        player.np = await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol'], description="Change the player volume.", usage="{prefix}volume <float between 1 and 100>")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def change_volume(self, ctx, *, vol: float):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send(embed=discord.Embed(title='Not connected to a voice channel.',  description=discord.Embed.Empty, color=0xff0000))
        if not 0 < vol < 101:
            return await ctx.send(embed=discord.Embed(title='Please enter a value between 1 and 100.',  description=discord.Embed.Empty, color=0xff0000))
        player = self.get_player(ctx)
        if vc.source:
            vc.source.volume = vol / 100
        player.volume = vol / 100
        await ctx.send(embed=discord.Embed(title=f'{ctx.author}: Set the volume to {vol}%',  description=discord.Embed.Empty, color=0xff0000))

    @commands.command(name='stop', aliases=['dc', 'disconnect'], description="Stop the player and clear the queue.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stop_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send(embed=discord.Embed(title='Nothing is Playing.',  description=discord.Embed.Empty, color=0xff0000))
        await self.cleanup(ctx.guild)
