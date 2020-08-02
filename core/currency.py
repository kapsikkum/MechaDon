import asyncio
import json

import aiohttp
import discord
from discord.ext import commands

import core
import core.exceptions
import core.utils


class Currency_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bal'], description="Check the balance of you or another person.", usage="{prefix}balance\n{prefix}balance @user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def balance(self, ctx, user: discord.User = None):
        if user is None:
            cash = await core.utils.check_cash(ctx.message.author.id)
            if cash is None:
                cash = await core.utils.add_user(ctx.message.author.id)
            await ctx.send(embed=discord.Embed(title="Current Balance:",  description=f"${(0 if cash is None else cash)}", color=0xff0000))
        else:
            cash = await core.utils.check_cash(user.id)
            if cash is None:
                cash = await core.utils.add_user(ctx.message.author.id)
            await ctx.send(embed=discord.Embed(title=f"Balance for {user.name}:",  description=f"${(0 if cash is None else cash)}", color=0xff0000))

    @commands.command(description="Collect your chatting bonus.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def collect(self, ctx):
        cash = await core.utils.check_cash(ctx.message.author.id)
        if cash is None:
            cash = await core.utils.add_user(ctx.message.author.id)
        cash = await core.utils.add_cash(ctx.message.author.id, core.user_currency[str(ctx.message.author.id)])
        await ctx.send(embed=discord.Embed(title=f"Collected ${round(core.user_currency[str(ctx.message.author.id)], 2)}",  description=f"Current Balance: ${cash}", color=0xff0000))
        core.user_currency[str(ctx.message.author.id)] = 0.0

    @commands.command(description="Collect your daily $250.")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        cash = await core.utils.check_cash(ctx.message.author.id)
        if cash is None:
            cash = await core.utils.add_user(ctx.message.author.id)
        cash = await core.utils.add_cash(ctx.message.author.id, 250.0)
        await ctx.send(embed=discord.Embed(title="Collected $250.0",  description=f"Current Balance: ${cash}", color=0xff0000))

    @commands.command(description="Buy items from a shop of your choice.", usage="{prefix}shop (To view available shops.)\n{prefix}shop <shop name> (To list items on that shop)\n{prefix}shop <shop name> buy <item number> (To buy an item)")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shop(self, ctx, store=None, mode=None, item=None):
        cash = await core.utils.check_cash(ctx.message.author.id)
        if cash is None:
            cash = await core.utils.add_user(ctx.message.author.id)
        stores = await core.utils.shop_catalog()
        if store is not None:
            if mode is not None:
                if mode == "buy":
                    if item is not None:
                        if store is not None:
                            if store in stores:
                                try:
                                    item = list(stores[store]['catalog'].keys())[int(item) - 1]
                                except:
                                    raise core.exceptions.CommandError("Not a Valid Shop item.")
                                else:
                                    purchase, catalog = await core.utils.purchase_item(ctx.message.author.id, stores[store]['catalog'], item)
                                    if purchase is None:
                                        await ctx.send(embed=discord.Embed(title=f"You don't have the funds for this.",  description="Get some cash loser poor boy", color=0xff0000))
                                    else:
                                        stores[store]['catalog'] = catalog
                                        await core.utils.shop_catalog(catalog=store, content=stores[store]['catalog'], mode="w")
                                        await ctx.send(embed=discord.Embed(title=f"Item Purchased.",  description="Sending you the item in DMs now.", color=0xff0000))
                                        embed = discord.Embed(title=f"{purchase['name']}",  description="Your item has arrived.", color=0xff0000)
                                        if purchase['type'] == "image":
                                            embed.set_image(url=purchase['product'])
                                        elif purchase['type'] == "text":
                                            embed.add_field(name=f"What you bought:", value=purchase['product'], inline=False)
                                        await ctx.message.author.send(embed=embed)
                            else:
                                await ctx.send(embed=discord.Embed(title="Invalid Store.",  description="Available stores:\n {stores}".format(stores='\n'.join(list(stores))), color=0xff0000))
            else:
                if store is not None:
                    if store in stores:
                        counter = 0
                        if stores[store]['nsfw']:
                            store_page = discord.Embed(
                                title=f"Shop: {store} (NSFW)",  description=discord.Embed.Empty, color=0xff0000)
                        else:
                            store_page = discord.Embed(title=f"Shop: {store}",  description=discord.Embed.Empty, color=0xff0000)
                        for item in list(stores[store]['catalog']):
                            counter += 1
                            if not ctx.channel.is_nsfw() and stores[store]['catalog'][item]['nsfw']:
                                store_page.add_field(
                                    name=f"**{counter}:**", value="**[NSFW]**", inline=False)
                            else:
                                store_page.add_field(
                                    name=f"**{counter}:**", value=f" ***__{item}__*** \nPrice: **${round(stores[store]['catalog'][item]['price'], 2)}**\n Quantity: {stores[store]['catalog'][item]['quantity'] if not stores[store]['catalog'][item]['permanent'] else '∞'}", inline=False)
                        if stores[store]['nsfw']:
                            if isinstance(ctx.channel, discord.DMChannel):
                                await ctx.send(embed=store_page)
                            elif ctx.channel.is_nsfw():
                                await ctx.send(embed=store_page)
                            else:
                                await ctx.send(embed=discord.Embed(title="This channel is not marked as NSFW",  description='Please do this command in a NSFW channel or DMs.', color=0xff0000))
                        else:
                            await ctx.send(embed=store_page)
                    else:
                        await ctx.send(embed=discord.Embed(title="Invalid Store.",  description="Available stores:\n {stores}".format(stores='\n'.join(list(stores))), color=0xff0000))
        else:
            await ctx.send(embed=discord.Embed(title="No store specified",  description="Available stores:\n {stores}".format(stores='\n'.join(list(stores))), color=0xff0000))

    @commands.command(description="Play the lotto. Costs $50.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def lotto(self, ctx):
        cash = await core.utils.check_cash(ctx.message.author.id)
        if cash is None:
            cash = await core.utils.add_user(ctx.message.author.id)
        purchase = await core.utils.remove_cash(ctx.message.author.id, 50)
        if purchase is None:
            await ctx.send(embed=discord.Embed(title=f"You don't have the funds for this.",  description="Get some cash loser poor boy", color=0xff0000))
        else:
            if core.utils.random.randint(1, 10) == 1:
                winnings = core.utils.random.uniform(55.0, 1000.0)
                await core.utils.add_cash(ctx.message.author.id, winnings)
                await ctx.send(embed=discord.Embed(title="You Won!",  description=f"Winnings: ${round(winnings, 2)}", color=0xff0000))
            else:
                await ctx.send(embed=discord.Embed(title="You Lost! 🙂",  description=f"-$50\nBetter luck next time.", color=0xff0000))

    @commands.command(description="Check the items you have bought.", usage="{prefix}items\n{prefix}items <item number>")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def items(self, ctx, view=None):
        cash = await core.utils.check_cash(ctx.message.author.id)
        if cash is None:
            cash = await core.utils.add_user(ctx.message.author.id)
        items = await core.utils.check_owned_items(ctx.message.author.id)
        if len(items) == 0:
            await ctx.send(embed=discord.Embed(title="You have no items.",  description="Buy some from the shop.", color=0xff0000))
        else:
            if view is None:
                items_embed = discord.Embed(title=f"Your items",  description=discord.Embed.Empty, color=0xff0000)
                counter = 0
                for item in items:
                    counter += 1
                    items_embed.add_field(name=f"{counter}.", value=f"***{items[item]['name']}***\nValue: **{items[item]['price']}**\nQuantity: **{items[item]['quantity']}**")
                await ctx.send(embed=items_embed)
            else:
                try:
                    item = list(items.keys())[int(view) - 1]
                except:
                    await ctx.send(embed=discord.Embed(title=f"Invalid Item.",  description="Select the right one next time.", color=0xff0000))
                else:
                    await ctx.send(embed=discord.Embed(title=f"OK.",  description="Sending you your item in DMs now.", color=0xff0000))
                    embed = discord.Embed(
                        title=f"{items[item]['name']}",  description="This is your item.", color=0xff0000)
                    if items[item]['type'] == "image":
                        embed.set_image(
                            url=items[item]['product'])
                    elif items[item]['type'] == "text":
                        embed.add_field(
                            name=f"Your Item:", value=items[item]['product'], inline=False)
                    await ctx.message.author.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def givecash(self, ctx, user: discord.User=None, amount=0):
        if not user:
            await ctx.send(embed=discord.Embed(title="No User Mentioned.",  description="Can't give cash to nobody can I?", color=0xff0000))
        else:
            if await core.utils.check_cash(user.id) is None:
                await core.utils.add_user(user.id)
            await core.utils.add_cash(user.id, float(amount))
            await ctx.send(embed=discord.Embed(title=f"Gave ${amount} to {user.name}.",  description="Ruining the economy I see.", color=0xff0000))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def setcash(self, ctx, user: discord.User = None, amount=0):
        if not user:
            await ctx.send(embed=discord.Embed(title="No User Mentioned.",  description="What are you dumb?", color=0xff0000))
        else:
            if await core.utils.check_cash(user.id) is None:
                await core.utils.add_user(user.id)
            await core.utils.set_cash(user.id, float(amount))
            await ctx.send(embed=discord.Embed(title=f"Set {user.name}'s balance to ${amount}.",  description="\"i am crippeld in debt rn bru\"\n- Mattlau04", color=0xff0000))

    @commands.group(hidden=True)
    @commands.is_owner()
    async def sellitem(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Invalid sub command given.", description="Dumbass can't use his own bot LMAO", color=0xff0000))

    @sellitem.command(hidden=True)
    @commands.is_owner()
    async def template(self, ctx):
        await ctx.send("```json\n" + json.dumps({"name": "Namehere", "type": "text", "product": "PRODUCT", "price": 0, "quantity": 5, "permanent": False, "nsfw": False}, indent=4) + "```")
    
    @sellitem.command(hidden=True)
    @commands.is_owner()
    async def add(self, ctx, name: str = None, *, data: str = None):
        if name is not None:
            if len(ctx.message.attachments) == 0:
                if data is not None:
                    item = json.loads(data)
                    await core.utils.shop_catalog(catalog="general", content=item, name=name, mode="a")
            else:
                attachment = ctx.message.attachments[0].url
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment) as r:
                        if r.status == 200:
                            item = json.loads(await r.text())
                            await core.utils.shop_catalog(catalog="general", content=item, name=name, mode="a")
        await ctx.send("ok")
