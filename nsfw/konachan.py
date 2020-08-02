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

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
home_page = "http://konachan.com/"


class KonaChanClient:
	def __init__(self, bot):
		self.cache = core.utils.Cache(bot)

	async def get_images(self, tag):
		images = list()
		if await self.cache.get(tag) is None:
			async with aiohttp.ClientSession() as session:
				async with session.get("http://konachan.com/post.json", params={"tags": tag, "limit": 100}, headers=headers) as response:
					if response.status == 200:
						data = await response.json()
						await self.cache.add(tag, data, delay=500)
						if data is not None:
							for post in data:
								try:
									if post['file_url'].split(".")[-1] in ['mp4', 'webm']:
										pass
									else:
										images.append({
											"file_url": post['file_url'],
											"post_url": f"https://konachan.com/post/show/{post['id']}"
										})
								except:
									pass
		else:
			data = await self.cache.get(tag)
			for post in data:
				try:
					if post['file_url'].split(".")[-1] in ['mp4', 'webm']:
						pass
					else:
						images.append({
							"file_url": post['file_url'],
							"post_url": f"https://konachan.com/post/show/{post['id']}"
						})
				except:
					pass
		return images
