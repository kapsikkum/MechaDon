# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 14:24:36
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-13 14:24:36
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
home_page = "https://rule34.xxx/"


class Rule34Client:
    def __init__(self, bot):
        self.cache = core.utils.Cache(bot)

    async def get_images(self, tag):
        images = list()
        if await self.cache.get(tag) is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://rule34.xxx/index.php",
                    params={
                        "page": "dapi",
                        "s": "post",
                        "q": "index",
                        "json": 1,
                        "tags": tag,
                    },
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        await self.cache.add(tag, data, delay=500)
                        if data is not None:
                            for post in data:
                                try:
                                    if post["image"].split(".")[-1] in ["mp4", "webm"]:
                                        pass
                                    else:
                                        images.append(
                                            {
                                                "file_url": f'{home_page}images/{post["directory"]}/{post["image"]}',
                                                "post_url": f'{home_page}index.php?page=post&s=view&id={post["id"]}',
                                            }
                                        )
                                except:
                                    pass
        else:
            data = await self.cache.get(tag)
            for post in data:
                try:
                    if post["image"].split(".")[-1] in ["mp4", "webm"]:
                        pass
                    else:
                        images.append(
                            {
                                "file_url": f'{home_page}images/{post["directory"]}/{post["image"]}',
                                "post_url": f'{home_page}index.php?page=post&s=view&id={post["id"]}',
                            }
                        )
                except:
                    pass
        return images
