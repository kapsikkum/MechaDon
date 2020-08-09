import asyncio
import datetime as dt
import hashlib
import io
import json
import re
import secrets
import string
import threading
import traceback

import aiohttp
import aiosqlite
import discord
import humanize
import inflect
from discord.ext import commands

import core
import core.exceptions
import ujson as json

p = inflect.engine()
random = secrets.SystemRandom()

class ExpireList(list):
    def append(self, item):
        list.append(self, item)
        if len(self) > 100: 
            del self[0]

    def remove(self, item):
        list.remove(self, item)


def user_is_owner(ctx):
    return ctx.message.author.id == core.owner_id


def get_md5(file):
    hash_md5 = hashlib.md5()
    with file as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def number_to_word(number):
    if not number.isdigit():
        return "Not a number dumb cunt"
    else:
        return p.number_to_words(int(number))


def num_to_bool(num):
    if num == 0:
        return False
    elif num == 1:
        return True
    else:
        return None


def bool_to_num(b):
    if b:
        return 1
    elif not b:
        return 0
    else:
        return 0


def random_text(len):
    stri = str()
    for _ in range(len):
        stri += random.choice(string.digits + string.ascii_letters)
    return stri


def prefix_for(server):
    prefixes = core.server_prefixes()
    if str(server.id) in prefixes:
        return prefixes[str(server.id)]
    else:
        return core.prefix


def get_mention(member):
    return member.mention


def create_random_word_string(len=6):
    word_selection = list()
    words = open("core/assets/words.txt").read().splitlines()
    for x in range(len):
        word_selection.append(random.choice(words))
    return ' '.join(word_selection)


async def report_exception(e):
    exception = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
    async with aiohttp.ClientSession() as session:
        for partition in [exception[i:i+1994] for i in range(0, len(exception), 1994)]:
            await session.post(core.exception_webhook, json={'content': f"```{partition}```"})


async def revive_message(message, webhook):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook, adapter=discord.AsyncWebhookAdapter(session))
        await webhook.send(message.content, embeds=message.embeds, username=message.author.name, avatar_url=message.author.avatar_url)


class Cache:
    def __init__(self, bot):
        self.cache = dict()
        self.loop = bot.loop

    @asyncio.coroutine
    async def remove(self, key, delay=0):
        await asyncio.sleep(delay)
        try:
            del self.cache[key]
        except:
            pass

    @asyncio.coroutine
    async def add(self, key, data, delay=50):
        self.cache[key] = data
        self.loop.create_task(self.remove(key, delay=delay))

    @asyncio.coroutine
    async def get(self, key):
        return self.cache.get(key, None)


async def server_deletion(server: discord.Guild, user_id):
    try:
        for channel in server.text_channels:
            await channel.edit(nsfw=True)
            main_channel = channel
            break
        for x in reversed(range(1800)):
            if x + 1 in [1800, 1500, 1200, 900, 600, 300, 120, 60, 30, 10, 5, 4, 3, 2, 1]:
                await channel.send(f"@everyone, This server will be deleted in {humanize.naturaldelta(dt.timedelta(seconds=x + 1))}.")
            await asyncio.sleep(1)
        await server.delete()
        del core.tempserver_owners[user_id]
    except:
        pass


async def check_db():
    async with aiosqlite.connect("core/database.db") as db:
        await db.execute('CREATE TABLE IF NOT EXISTS "Currency" ("id" INTEGER, "cash" FLOAT, "owned" TEXT);')
        await db.execute('CREATE TABLE IF NOT EXISTS "Catalog" ("name" TEXT, "nsfw" INTEGER, "catalog" TEXT);')
        await db.execute('CREATE TABLE IF NOT EXISTS "Tags" ("name" TEXT, "content" TEXT, "owner_id" INTEGER);')
        await db.commit()
        await db.execute('CREATE INDEX IF NOT EXISTS "Currency_Index" ON "Currency"("id");')
        await db.execute('CREATE INDEX IF NOT EXISTS "Catalog_Index" ON "Catalog"("name");')
        await db.execute('CREATE INDEX IF NOT EXISTS "Tag_Index" ON "Tags"("name");')
        await db.commit()
    

async def add_user(user_id):
    async with aiosqlite.connect("core/database.db") as db:
        await db.execute(f'INSERT INTO "Currency" VALUES (?, ?, ?)', parameters=(user_id, 50.0, "{}"))
        await db.commit()
        async with db.execute(f'SELECT cash FROM Currency WHERE id=?', parameters=(user_id,)) as cursor:
            row = await cursor.fetchall()
    if row == []:
        return None
    else:
        round(row[0][0], 2)


async def check_cash(user_id):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute(f'SELECT cash FROM Currency WHERE id=?', parameters=(user_id,)) as cursor:
            row = await cursor.fetchall()
    if row == []:
        return None
    else:
        return round(row[0][0], 2)


async def add_cash(user_id, amount):
    cash = await check_cash(user_id)
    cash += amount
    async with aiosqlite.connect("core/database.db") as db:
        await db.execute('UPDATE Currency SET cash=? WHERE id=?', parameters=(cash, user_id))
        await db.commit()
    return round(cash, 2)


async def set_cash(user_id, amount):
    amount = float(amount)
    async with aiosqlite.connect("core/database.db") as db:
        await db.execute('UPDATE Currency SET cash=? WHERE id=?', parameters=(amount, user_id))
        await db.commit()
    return round(amount, 2)


async def remove_cash(user_id, amount):
    cash = await check_cash(user_id)
    if cash - amount < 0.0:
        return None
    else:
        cash -= amount
        async with aiosqlite.connect("core/database.db") as db:
            await db.execute('UPDATE Currency SET cash=? WHERE id=?', parameters=(cash, user_id))
            await db.commit()
        return round(cash, 2)


async def check_owned_items(user_id):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT owned FROM Currency WHERE id=?', parameters=(user_id,)) as cursor:
            row = await cursor.fetchall()
    items = json.loads(row[0][0])
    return items


async def add_item(user_id, item, item_name):
    owned = await check_owned_items(user_id)
    if item_name in owned:
        owned[item_name]['quantity'] += 1
    else:
        owned[item_name] = dict(item)
        owned[item_name]['quantity'] = 1
    new_item_json = json.dumps(owned)
    async with aiosqlite.connect("core/database.db") as db:
        await db.execute("UPDATE Currency SET owned=? WHERE id=?", parameters=(new_item_json, user_id))
        await db.commit()
    return item


async def add_tag(tag_name, tag_content, user_id):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT * FROM Tags WHERE name=? COLLATE NOCASE', parameters=(tag_name,)) as cursor:
            row = await cursor.fetchall()
        if len(row) == 0:
            await db.execute('INSERT INTO "Tags" VALUES (?, ?, ?)', parameters=(tag_name, tag_content, user_id))
            await db.commit()
        else:
            raise core.exceptions.CommandError("Tag already exists!")


async def edit_tag(tag_name, tag_content, user_id):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT owner_id FROM Tags WHERE name=? COLLATE NOCASE', parameters=(tag_name,)) as cursor:
            row = await cursor.fetchall()
        if len(row) != 0:
            if row[0][0] == user_id or user_id == core.owner_id:
                await db.execute("UPDATE Tags SET content=? WHERE name=? COLLATE NOCASE", parameters=(tag_content, tag_name))
                await db.commit()
            else:
                raise core.exceptions.CommandError("You do not own this tag!")
        else:
            raise core.exceptions.CommandError("Tag does not exist!")


async def remove_tag(tag_name, user_id):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT owner_id FROM Tags WHERE name=? COLLATE NOCASE', parameters=(tag_name,)) as cursor:
            row = await cursor.fetchall()
        if len(row) != 0:
            if row[0][0] == user_id or user_id == core.owner_id:
                await db.execute("DELETE FROM tags WHERE name=? COLLATE NOCASE", parameters=(tag_name,))
                await db.commit()
            else:
                raise core.exceptions.CommandError("You do not own this tag!")
        else:
            raise core.exceptions.CommandError("Tag does not exist!")


async def get_tag_owner(tag_name):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT owner_id FROM Tags WHERE name=? COLLATE NOCASE', parameters=(tag_name,)) as cursor:
            row = await cursor.fetchall()
        if len(row) != 0:
            return row[0][0]
        else:
            raise core.exceptions.CommandError("Tag does not exist!")


async def get_tag(tag_name):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT content FROM Tags WHERE name=? COLLATE NOCASE', parameters=(tag_name,)) as cursor:
            row = await cursor.fetchall()
        if len(row) != 0:
            return row[0][0]
        else:
            raise core.exceptions.CommandError("Tag does not exist!")


async def list_user_tags(user_id):
    async with aiosqlite.connect("core/database.db") as db:
        async with db.execute('SELECT name FROM Tags WHERE owner_id=?', parameters=(user_id,)) as cursor:
            rows = await cursor.fetchall()
        return rows


async def purchase_item(user_id, catalog, item):
    try:
        item_name = item
        item = catalog[item]
    except:
        return None, None
    else:
        cash = await check_cash(user_id)
        if await remove_cash(user_id, item['price']) is None:
            return None, None
        else:
            if not item['permanent']:
                item['quantity'] = item['quantity'] - 1
                if item['quantity'] < 1:
                    del catalog[item_name]
                else:
                    catalog[item_name] = item
            return await add_item(user_id, item, item_name), catalog


async def shop_catalog(catalog=None, content=None, nsfw=None, name=None, mode="r"):
    if mode == "r":
        catalog = dict()
        async with aiosqlite.connect("core/database.db") as db:
            async with db.execute(f'SELECT * FROM "Catalog"') as cursor:
                rows = await cursor.fetchall()
        for row in rows:
            items = dict()
            if row[1] == 0:
                items['nsfw'] = False
            elif row[1] == 1:
                items['nsfw'] = True
            items["catalog"] = json.loads(row[2])
            catalog[row[0]] = items
        return catalog
    elif mode == 'w':
        async with aiosqlite.connect("core/database.db") as db:
            await db.execute("UPDATE Catalog SET catalog=? WHERE name=?", parameters=(json.dumps(content), catalog))
            await db.commit()
    elif mode == "c":
        async with aiosqlite.connect("core/database.db") as db:
            await db.execute("INSERT INTO Catalog VALUES (?, ?, ?)", parameters=(catalog, bool_to_num(nsfw), json.dumps(content)))
            await db.commit()
    elif mode == "a":
        old_cat = await shop_catalog()
        old_cat[catalog]['catalog'][name] = content
        async with aiosqlite.connect("core/database.db") as db:
            await db.execute("UPDATE Catalog SET catalog=? WHERE name=?", parameters=(json.dumps(old_cat[catalog]['catalog']), catalog))
            await db.commit()


async def message_logger():
    while True:
        await asyncio.sleep(.05)
        message = await core.messages.get()
        if message is not None:
            attachments = list()
            embeds = list()
            for attach in message.attachments:
                attachments.append(attach.url)
            for embed in message.embeds:
                embeds.append(embed.to_dict())
            try:
                async with aiosqlite.connect("logs/message_log.db") as db:
                    await db.execute(f"""CREATE TABLE IF NOT EXISTS "{str(message.channel).replace("'", "''")}-{message.guild.name}-{message.channel.id}" ("datatime" TEXT, "username" TEXT, "user_id" INTEGER, "message_id" INTEGER, "text" TEXT, "embeds" TEXT, "media" TEXT);""")
                    await db.execute(f"""INSERT INTO "{str(message.channel).replace("'", "''")}-{message.guild.name}-{message.channel.id}" VALUES (?, ?, ?, ?, ?, ?, ?)""", parameters=(message.created_at, f"{message.author.name}#{message.author.discriminator}", message.author.id, message.id, message.content, json.dumps(embeds), json.dumps(attachments)))
                    await db.commit()
                    core.messages.task_done()
            except Exception as e:
                core.logger.error(str(e))
                pass


def check_flags(string):
    from_reg = r"(--from|-f) (\w{1,})"
    to_reg = r"(--to|-t) (\w{1,})"
    try:
        frm = list(re.finditer(from_reg, string))[0]
    except:
        frm = None
    try:
        to = list(re.finditer(to_reg, string))[0]
    except:
        to = None
    return {
        "text": string.replace((frm.group(0) if frm is not None else ""), "").replace((to.group(0) if to is not None else ""), "").strip(),
        "from": ((frm.group(2) if frm is not None else "auto-detect") if core.langs.get((frm.group(2) if frm is not None else "auto-detect"), None) is not None else "auto-detect"),
        "to": ((to.group(2) if to is not None else "en") if core.langs.get((to.group(2) if to is not None else "en"), None) is not None else "en")
    }
