import asyncio
import io
import re
import time
from datetime import datetime, timedelta

import aiohttp
import discord
import humanize
from dateutil import tz
from discord.ext import commands

import core
import core.exceptions
import core.utils


class Basic_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Shows the help message.", usage="{prefix}help\n{prefix}help <command name>")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def help(self, ctx, cmd=None):
        if cmd is None:
            if ctx.message.guild is not None:
                embed = discord.Embed(title="Bot Commands", description=f"Prefix for this server is {core.utils.prefix_for(ctx.message.guild)}\nUse {core.utils.prefix_for(ctx.message.guild)}help <command> for more info.\nBot Version: {core.__version__}", color=0xff0000)
            else:
                embed = discord.Embed(title="Bot Commands", description=f"Prefix is {core.prefix}\nUse {core.prefix}help <command> for more info.\nBot Version: {core.__version__}", color=0xff0000)
            categories = dict()
            for command in self.bot.commands:
                if command.hidden:
                    pass
                else:
                    if command.cog_name in categories:
                        categories[command.cog_name].append(command)
                    else:
                        categories[command.cog_name] = list()
                        categories[command.cog_name].append(command)
            for category in sorted(categories):
                commandlist = list()
                for command in categories[category]:
                    commandlist.append(command.name)
                if ctx.message.guild is not None:
                    embed.add_field(name=f"**__{category.replace('_', ' ')}__**", value="\n".join(
                        [f"**{core.utils.prefix_for(ctx.message.guild)}{command}**" for command in sorted(commandlist)]), inline=True)
                else:
                    embed.add_field(name=f"**__{category.replace('_', ' ')}__**", value="\n".join(
                        [f"**{core.prefix}{command}**" for command in sorted(commandlist)]), inline=True)
            await ctx.send(embed=embed)
        else:
            com = None
            for command in self.bot.commands:
                if com is not None:
                    break
                if cmd == command.name:
                    com = command
                for alias in command.aliases:
                    if cmd == alias:
                        com = command
            if com is None:
                raise core.exceptions.CommandError("Command does not exist.")
            else:
                if com.hidden:
                    raise core.exceptions.CommandError("Command does not exist.")
                else:
                    if ctx.message.guild is not None:
                        embed = discord.Embed(title=f"Command info for {core.utils.prefix_for(ctx.message.guild)}{com.name}", description=discord.Embed.Empty, color=0xff0000)
                    else:
                        embed = discord.Embed(title=f"Command info for {core.prefix}{com.name}", description=discord.Embed.Empty, color=0xff0000)
                    if com.description == "":
                        embed.add_field(name="**Description:**",
                                        value="No Description.", inline=False)
                    else:
                        embed.add_field(name="**Description:**",
                                        value=com.description, inline=False)
                    if len(com.aliases) > 0:
                        embed.add_field(name="**Aliases:**", value=', '.join(sorted(com.aliases)), inline=False)
                    if com.usage is None:
                        if ctx.message.guild is not None:
                            embed.add_field(name="**Usage:**", value=f"{core.utils.prefix_for(ctx.message.guild)}{com.name}", inline=False)
                        else:
                            embed.add_field(name="**Usage:**", value=f"{core.prefix}{com.name}", inline=False)
                    else:
                        if ctx.message.guild is not None:
                            embed.add_field(name="**Usage:**", value=str(com.usage).format(prefix=core.utils.prefix_for(ctx.message.guild)), inline=False)
                        else:
                            embed.add_field(name="**Usage:**", value=str(com.usage).format(prefix=core.prefix), inline=False)
                    await ctx.send(embed=embed)
      
    @commands.command(description="Pings the bot (Don't)")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        await ctx.send(f"Shut the fuck up ||({int(self.bot.latency * 1000)} ms)||")

    @commands.command(description="Gets info on a specified user.", usage="{prefix}whois @user", aliases=['userinfo'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def whois(self, ctx, user=None):
        if user is None:
            user = str(ctx.author.mention)
        user = re.search("[0-9]{18}", user)
        if user:
            user = user.group(0)
            try:
                user = await self.bot.fetch_user(user)
            except:
                raise core.exceptions.CommandError("Unable to find that user.")
            try:
                user_member = ctx.message.guild.get_member(user.id)
                if user_member is None:
                    raise Exception
            except:
                embed = discord.Embed(title=f"Info on {user.name}",  description="", color=0xff0000)
                embed.set_thumbnail(url=user.avatar_url)
                embed.add_field(name="**Username**", value=f"{user.name}#{user.discriminator}", inline=False)
                embed.add_field(name="**Other info**",
                                value=f"**Bot**: {user.bot}\n**ID**: {user.id}")
                embed.add_field(
                    name="**Timestamps**", value=f"**Account Created**: {user.created_at.strftime('%d/%m/%Y %I:%M %p')} ({humanize.naturaltime(user.created_at)})", inline=False)
            else:
                user = user_member
                embed = discord.Embed(title=f"Info on {user.name}",  description="", color=0xff0000)
                embed.set_thumbnail(url=user.avatar_url)
                embed.add_field(name="**Username**", value=f"{user.name}#{user.discriminator}", inline=False)
                embed.add_field(name="**Nickname**", value=user.nick, inline=True)
                statusstr = str()
                statusstr += f"**On Mobile**: {user.is_on_mobile()}\n"
                statusstr += f"**Account**: {user.status.name}\n"
                statusstr += f"**Desktop**: {user.desktop_status.name}\n"
                statusstr += f"**Mobile**: {user.mobile_status.name}\n"
                statusstr += f"**Web/Other**: {user.web_status.name}\n"
                embed.add_field(name="**Statuses**", value=statusstr, inline=False)
                embed.add_field(name="**Other info**", value=f"**Bot**: {user.bot}\n**ID**: {user.id}")
                joined_at = user.joined_at.replace(tzinfo=tz.gettz('UTC'))
                created_at = user.created_at.replace(tzinfo=tz.gettz('UTC'))
                embed.add_field(
                    name="**Timestamps**", value=f"**Date Joined**: {user.joined_at.strftime('%d/%m/%Y %I:%M %p')} ({humanize.naturaltime(datetime.now().replace(tzinfo=tz.tzlocal()) - joined_at.astimezone(tz.tzlocal()))})\n**Account Created**: {user.created_at.strftime('%d/%m/%Y %I:%M %p')} ({humanize.naturaltime(datetime.now().replace(tzinfo=tz.tzlocal()) - created_at.astimezone(tz.tzlocal()))})", inline=False)
            await ctx.send(embed=embed)
        else:
            raise core.exceptions.CommandError("Not a user.\n~~||Shits fucked.||~~")

    @commands.command(description="Gets info on a specified invite.", usage="{prefix}inviteinfo https://discord.gg/cumzone | discord.gg/cumzone | cumzone", aliases=['invinf'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def inviteinfo(self, ctx, inv: discord.Invite = None):
        if inv is not None:
            inv = await self.bot.fetch_invite(inv.id, with_counts=True)
            embed = discord.Embed(title=f"Info on invite to {inv.guild.name}",  description=discord.Embed.Empty, color=0xff0000)
            embed.set_thumbnail(url=inv.guild.icon_url)
            embed.add_field(name="**Server Info**", value=f"**Name**: {inv.guild.name}\n**ID**: {inv.guild.id}\n**Members**: {inv.approximate_member_count} ({inv.approximate_presence_count} online)", inline=False)
            embed.add_field(name="**Invite Info**", 
                            value=f"**URL**: {inv.url}\n**Code**: {inv.id}\n**Channel Name**: {inv.channel.name}\n**Channel ID**: {inv.channel.id}\n**Channel Type**: {inv.channel.type}", inline=False)
            if inv.inviter is not None:
                embed.add_field(name="**Inviter Info**",
                                value=f"**User**: {inv.inviter.name}#{inv.inviter.discriminator}\n**ID**: {inv.inviter.id}\n**Bot**: {inv.inviter.bot}\n[Avatar]({inv.inviter.avatar_url})", inline=False)
                embed.set_footer(text=inv.inviter.name, icon_url=inv.inviter.avatar_url)
            await ctx.send(embed=embed)
        else:
            raise core.exceptions.CommandError("No invite given.")

    @commands.command(description="Make the bot say something.", usage="{prefix}say <message>")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def say(self, ctx, *args):
        await ctx.send(" ".join(args).replace("@everyone", "@nobody").replace("@here", "@there"))

    @commands.command(description="Make a random string of words.", aliases=['rw', 'ranword'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def randomwords(self, ctx, length: int = 10):
        if length > 500:
            length = 500
        words = core.utils.create_random_word_string(len=length)
        for partition in [words[i:i+2000] for i in range(0, len(words), 2000)]:
            await ctx.send(embed=discord.Embed(title=discord.Embed.Empty,  description=partition, color=0xff0000))

    @commands.command(aliases=['saynum'], description="Convert a number into words.", usage="{prefix}saynumber <number>")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def saynumber(self, ctx, number):
        await ctx.send(embed=discord.Embed(title=f"{number} in words:",  description=core.utils.number_to_word(number), color=0xff0000))

    @commands.command(hidden=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vore(self, ctx, user: discord.Member = None):
        if ctx.message.author.id == user.id:
            embed = discord.Embed(title="Oh...",  description=r"Ť̫̣̬͓̹͙͚̹̖̬̹̬̹̟̙̼̥͖ͭ̇͐̅ͨ̋ͮ̌͆̍ͨ̓ͥ͢͠H̨̧͚̳̖̲͓̫̘̲͉͍̼̞͋̂͌̾̕͟E̡ͦ́̀ͨͬ̋ͪ̈́͆̍͂̋͊ͭ̐̕͠҉̯̬̗͔̜͍͚̟͙ ͈̳̺̳̖̩̯͙̜̔ͪ́ͮ̿͟͟V̶̸̪̬͕̗̙̳͕̊ͨͫ͛̈ͭ͊ͬ̏ͨͦͥ̀̚͜͜Ōͭ͌͊͊̃͑̈́̓͌́̐̊̾̿̇̓̒͏̖̯͇̰̪̹̱̕I̸̍ͬ̇̎̈́̃̎̉̃͑̀͆̅́̏̋͂ͨ̚͘͝҉̥̞̖̩̹̬̹̭̤͎D̵̢̬̲̩͈̈́ͪͨ̋͐͒͟͞͞ ̸̄̄ͬ͑͗́ͩ́͝͏̠͕̯͍̪̮͠ͅĜ̸̰̖̳͇͓̰̹̹̩̟̣̖͎̦̙ͪͦ͌̃̆͒͟͜͞R̡̭̰̪͈̻̪͇̠͑ͯ̈̈́̎͆ͩ̉̄̀̀̋̋̅̅ͧ̎͂̚͘͘͟͟Ȍ̷̡̫͈̪̞̯̃̎̊̓͢Wͨ͂͋ͥ̽̈́̈͗͒ͬͬ̈ͧ̉̏̇͊҉҉̯̩͕̭̣͎̮̫̀S̡̛͍̮̹̲͇̘̘͎̬̱̻͈̼̀̽̇̄͌͑̎ͧ̾ͩ͐̅͂̉̐̓̀͡͝ͅ", color=0xff0000)
            embed.set_image(url="https://cdn.discordapp.com/attachments/686523390806327314/700731647988990042/8FuH.png")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Vore",  description=f"{ctx.message.author.name} has vored {user.name}!", color=0xff0000)
            embed.set_image(url="https://cdn.discordapp.com/attachments/686523390806327314/698912529493000212/fastvore.gif")
            await ctx.send(embed=embed)

    @commands.command(hidden=True, aliases=['murder'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kill(self, ctx, user: discord.Member = None):
        if ctx.message.author.id == user.id:
            embed = discord.Embed(title="Suicide",  description=f"{ctx.message.author.name} killed themselves LMAO", color=0xff0000)
            embed.set_image(url="https://cdn.discordapp.com/attachments/686523390806327314/700730485407481906/killself.gif")
            await ctx.send(embed=embed)
        else:
            actions = ['shot', 'annihilated', 'smashed', 'burned', 'brutally bumfucked', 'stabbed', 'stomped', 'tore appart', 'beat', 'hung', 'ate']
            results = ['dead', 'to death', 'to near death', 'to beyond recognition', 'to hell', 'into the ground', 'to peices']
            locations = ['in front of', 'behind', 'on top of', 'inside of', 'beside of', 'with', 'underneath of']
            persons = ['their family', 'their doctor', 'Mattlau04', 'Hatsune Miku', 'some random old guy', 'YandereDev', 'a daycare', 'a child', 'a school', 'some anime girls', 'tiffy', 'a fursuit', 'a furry', 'DeadBread76']
            sayings = ['SAD!', 'lmao', 'Good.', 'cum sex mmmmm', 'Fuck.', 'Yikes.', 'hectic.', 'cool!']
            images = ['https://cdn.discordapp.com/attachments/686523390806327314/698491736892112906/tenor_2.gif', 
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742929979015268/tenor.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742934391291964/tenor_6.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742936727519333/tenor_3.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742946626076802/tenor_2.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742945812381816/tenor_4.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742951780745256/tenor_5.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/700742964871299072/tenor_1.gif',
                      'https://cdn.discordapp.com/attachments/686523390806327314/698912529493000212/fastvore.gif',
                      'https://media.discordapp.net/attachments/680748917511421959/714395834514407495/Shion-Rock.gif']
            embed = discord.Embed(title="Murder",  description=f"**{ctx.message.author.name}** {core.utils.random.choice(actions)} **{user.name}** {core.utils.random.choice(results)} {core.utils.random.choice(locations)} {core.utils.random.choice(persons)}. {core.utils.random.choice(sayings)}", color=0xff0000)
            embed.set_image(url=core.utils.random.choice(images))
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def botinfo(self, ctx):
        embed = discord.Embed(title="Bot Info",  description=f"Member of **{len(self.bot.guilds)}** Guild(s)", color=0xff0000)
        embed.add_field(name="**Bot Version**", value=core.__version__, inline=False)
        embed.add_field(name="**Uptime**", value=timedelta(seconds=int(time.time()) - int(core.uptime)), inline=False)
        try: embed.add_field(name="**Prefix for guild**", value=core.utils.prefix_for(ctx.message.guild), inline=False)
        except: pass
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.cooldown(1, 31556952000, commands.BucketType.user)
    async def die(self, ctx):
        await ctx.send("No.")

    @commands.command(hidden=True, name="666")
    @commands.cooldown(0, 21016930032, commands.BucketType.user)
    async def _666(self, ctx):
        pass

    @commands.command(hidden=True, name="domino'sappfeathatsunemiku")
    @commands.cooldown(1, 666, commands.BucketType.user)
    async def domino(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/680748917511421959/710129074294751252/splash.mp4")

