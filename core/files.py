import asyncio
import io
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from zipfile import ZipFile

import aiofiles
import aiohttp
import discord
from discord.ext import commands
from PIL import Image, ImageDraw
from pydub import AudioSegment

import core
import core.exceptions
import core.utils


class File_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Checks MD5 of an uploaded file.", usage="{prefix}md5 <attachment>", name="md5", aliases=['checkmd5'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _md5(self, ctx):
        if len(ctx.message.attachments) == 0:
            raise core.exceptions.CommandError("No File Attached.")
        else:
            message = await ctx.send(embed=discord.Embed(title="Please Wait",  description="Checking File...", color=0xff0000))
            attachment = ctx.message.attachments[0].url
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment) as r:
                    if r.status == 200:
                        buffer = io.BytesIO(await r.read())
                        buffer.seek(0, 0)
                        md5 = core.utils.get_md5(buffer)
                        await message.edit(embed=discord.Embed(title=f"MD5 of {attachment.split('/')[-1]}:",  description=md5, color=0xff0000))
                    else:
                        raise core.exceptions.CommandError("An error occured.")

    @commands.command(description="Create a solid colour image from a hex value.", usage="{prefix}colour <hex value>", aliases=['color'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def colour(self, ctx, colour=None):
        if colour is not None:
            with tempfile.TemporaryDirectory() as tempdir:
                im = Image.new("RGB", (300, 300), colour)
                filename = f"{tempdir}/{uuid.uuid4()}.png"
                im.save(filename)
                file = discord.File(filename, filename=filename.split("/")[-1])
                embed = discord.Embed(title=f"Colour {colour}", color=0xff0000)
                embed.set_image(url=f"attachment://{filename.split('/')[-1]}")
                await ctx.send(file=file, embed=embed)
        else:
             raise core.exceptions.CommandError("No Colour Given.")


    @commands.command(description="Create a random colour image.", aliases=['randomcolor', 'rdmc'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def randomcolour(self, ctx):
        colour = '#%02x%02x%02x' % (core.utils.random.randint(0, 255), core.utils.random.randint(0, 255), core.utils.random.randint(0, 255))
        with tempfile.TemporaryDirectory() as tempdir:
            im = Image.new("RGB", (300, 300), colour)
            filename = f"{tempdir}/{uuid.uuid4()}.png"
            im.save(filename)
            file = discord.File(filename, filename=filename.split("/")[-1])
            embed = discord.Embed(title=f"Colour {colour}", color=0xff0000)
            embed.set_image(url=f"attachment://{filename.split('/')[-1]}")
            await ctx.send(file=file, embed=embed)


    @commands.command(description="Create a Don", usage="{prefix}don <optional hex colour>", aliases=['randon'])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def don(self, ctx, colour="random"):
        colour = colour.lstrip('#')
        if colour == "random":
            colour = '%02x%02x%02x' % (core.utils.random.randint(0, 255), core.utils.random.randint(0, 255), core.utils.random.randint(0, 255))
        colour = list(int(colour[i:i+2], 16) for i in (0, 2, 4))
        colour.append(255)
        colour = tuple(colour)
        with ctx.typing():
            background = Image.new('RGBA', (500, 500), (255, 0, 0, 0))
            back_colour = ImageDraw.Draw(background)
            back_colour.ellipse([(50, 50), (450, 450)], fill=colour)
            face = Image.open("core/assets/don.png")
            background.paste(face, (0,0), face)
            with tempfile.TemporaryDirectory() as tempdir:
                filename = f'{tempdir}/{uuid.uuid4()}.png'
                background.save(filename, "PNG")
                file = discord.File(filename, filename=filename.split("/")[-1])
                embed = discord.Embed(title="Da-don", description=f"HEX: `{'%02x%02x%02x' % (colour[0], colour[1], colour[2])}`", color=0xff0000)
                embed.set_image(url=f"attachment://{filename.split('/')[-1]}")
                await ctx.send(file=file, embed=embed)

    @commands.command(description="Create a .zip file full of random Dons.", usage="{prefix}massdon <optional number of dons>", aliases=['zipdon'])
    @commands.cooldown(1, 240, commands.BucketType.user)
    async def massdon(self, ctx, amount=None):
        try:
            amount = int(amount)
        except:
            amount = 10
        with ctx.typing():
            with tempfile.TemporaryDirectory() as tempdir:
                zipname = f'{tempdir}/{uuid.uuid4()}.zip'
                with ZipFile(zipname, 'w') as zip_file:
                    if amount > 175:
                        amount = 175
                        await ctx.send(embed=discord.Embed(title="Way too many dons!", description=f"Max is {amount}, so i'm only making that many.", color=0xff0000))
                    core.logger.info(f"Creating {amount} dons.")
                    for x in range(amount):
                        background = Image.new('RGBA', (500, 500), (255, 0, 0, 0))
                        back_colour = ImageDraw.Draw(background)
                        back_colour.ellipse([(50, 50), (450, 450)], fill=(core.utils.random.randint(0, 255), core.utils.random.randint(0, 255), core.utils.random.randint(0, 255), 255))
                        face = Image.open("core/assets/don.png")
                        background.paste(face, (0, 0), face)
                        filename = f'{tempdir}/{uuid.uuid4()}.png'
                        background.save(filename, "PNG")
                        zip_file.write(filename, f'{uuid.uuid4()}.png')
                file = discord.File(zipname, filename=f"dons-{uuid.uuid4()}.zip")
                await ctx.send(file=file)

    @commands.command(description="Creates Text To Speech .mp3 file (From Google)", usage="{prefix}tts <text>")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def tts(self, ctx, *, args):
        params = {
            "text": "".join(list(args)).replace('"', '').replace("'", ""),
            "enc": "mpeg",
            "lang": "en-us",
            "speed": "0.5",
            "client": "lr-language-tts",
            "use_google_only_voices": 1
        }
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.google.com/speech-api/v1/synthesize", params=params) as r:
                    if r.status == 200:
                        with tempfile.TemporaryDirectory() as tempdir:
                            async with aiofiles.open(f'{tempdir}/{ctx.message.author.id}.mp3', mode='wb') as f:
                                await f.write(await r.read())
                            await ctx.send(file=discord.File(f'{tempdir}/{ctx.message.author.id}.mp3', filename=f'{ctx.message.author.id}.mp3'))
                    else:
                        raise core.exceptions.CommandError(f"API error {r.status}")


    @commands.command(description="Expand Dong", usage="{prefix}bonzi <text>")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bonzi(self, ctx, *, args):
        params = {
            "text": "".join(list(args)).replace('"', '').replace("'", ""),
            "voice": "Adult Male #2, American English (TruVoice)",
            "pitch": 140,
            "speed": 157
        }
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://tetyys.com/SAPI4/SAPI4", params=params) as r:
                    if r.status == 200:
                        with tempfile.TemporaryDirectory() as tempdir:
                            sound = await self.bot.loop.run_in_executor(ThreadPoolExecutor(), AudioSegment.from_file, io.BytesIO(await r.read()), "wav")
                            await self.bot.loop.run_in_executor(ThreadPoolExecutor(), sound.export, f'{tempdir}/{ctx.message.author.id}.mp3', "mp3")
                            await ctx.send(file=discord.File(f'{tempdir}/{ctx.message.author.id}.mp3', filename=f'{ctx.message.author.id}.mp3'))
                    else:
                        raise core.exceptions.CommandError(f"API error {r.status}")
