# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 14:24:11
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-13 14:24:11
import asyncio
import hashlib
import io
import json
import random
import re
import urllib.parse

import aiohttp
import aiosqlite
import discord
import inflect
from bs4 import BeautifulSoup
from discord.ext import commands

import core
import core.exceptions
import core.utils

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
}
home_page = "https://danbooru.donmai.us/"


class DanbooruClient:
    def __init__(self, bot):
        self.cache = core.utils.Cache(bot)
        bot.loop.create_task(self.update_catalog_task())

    async def get_images(self, tag):
        images = list()
        if await self.cache.get(tag) is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://danbooru.donmai.us/posts.json",
                    params={"tags": tag, "limit": 100},
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self.cache.add(tag, data, delay=500)
                        if data is not None:
                            for post in data:
                                try:
                                    if post["file_url"].split(".")[-1] in [
                                        "mp4",
                                        "webm",
                                    ]:
                                        pass
                                    else:
                                        images.append(
                                            {
                                                "file_url": post["file_url"],
                                                "post_url": f"https://danbooru.donmai.us/posts/{post['id']}",
                                            }
                                        )
                                except:
                                    pass
        else:
            data = await self.cache.get(tag)
            for post in data:
                try:
                    if post["file_url"].split(".")[-1] in ["mp4", "webm"]:
                        pass
                    else:
                        images.append(
                            {
                                "file_url": post["file_url"],
                                "post_url": f"https://danbooru.donmai.us/posts/{post['id']}",
                            }
                        )
                except:
                    pass
        return images

    async def get_latest_posts(self):
        images = dict()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                home_page + "/posts?tags=rating%3Aexplicit+&ms=1", headers=headers
            ) as response:
                if response.status == 200:
                    page_html = await response.text()
                    soup = BeautifulSoup(page_html, "lxml")
                    div = soup.find("div", id="posts")
                    for post in div.find_all("article"):
                        if post.get("data-id", None) is not None:
                            tags = post.get("data-tags", "").split(" ")
                            source = f"{home_page}posts/{post.get('data-id', None)}"
                            img = post.get("data-file-url", None)
                            async with session.get(source, headers=headers) as response:
                                if response.status == 200:
                                    page_html = await response.text()
                                    soup = BeautifulSoup(page_html, "lxml")
                                    title = (
                                        soup.find("title")
                                        .string.replace(" | Danbooru", "")
                                        .replace("'", "")
                                        .replace('"', "")
                                    )
                                    images[title] = {
                                        "name": title,
                                        "type": "image",
                                        "product": img,
                                        "price": 1.5 * len(tags),
                                        "quantity": random.randint(5, 10),
                                        "permanent": False,
                                        "nsfw": True,
                                    }
        return images

    async def update_catalog_task(self):
        while True:
            content = await self.get_latest_posts()
            if not "danbooru" in list(await core.utils.shop_catalog()):
                await core.utils.shop_catalog(
                    catalog="danbooru", nsfw=True, content=content, mode="c"
                )
            else:
                await core.utils.shop_catalog(
                    catalog="danbooru", content=content, mode="w"
                )
            await asyncio.sleep(3600)


# async def image_fill_task():
# 	while True:
# 		for tag in list(core.danbooru_nsfw_images):
# 			core.danbooru_nsfw_images[tag]['images'] = await get_images(core.danbooru_nsfw_images[tag]['tag'])
# 			await asyncio.sleep(5)
# 		await asyncio.sleep(1800)
