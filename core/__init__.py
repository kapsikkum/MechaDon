# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 14:23:31
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-14 23:16:29
import asyncio
import json
import logging
import os
import sys
import time

import discord

__version_info__ = (2, 10, 8)
__version__ = ".".join(map(str, __version_info__))
config = json.load(open("config.json"))
token = config["token"]
prefix = config["prefix"]
debug_mode = config["debug_mode"]
exception_webhook = config["exception_webhook"]
uptime = time.time()

# Values

if not os.path.isfile("core/bonus.json"):
    with open("core/bonus.json", mode="w") as f:
        pass
user_currency = json.load(open("core/bonus.json"))
censor_check = dict()
deletions = dict()
nodelete_chans = list()
tempserver_owners = dict()
messages = asyncio.Queue()
langs = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bn-BD": "Bangla",
    "bs-Latn": "Bosnian (latin)",
    "bg": "Bulgarian",
    "yue": "Cantonese (Traditional)",
    "ca": "Catalan",
    "zh-Hans": "Chinese Simplified",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "et": "Estonian",
    "fj": "Fijian",
    "fil": "Filipino",
    "fi": "Finnish",
    "fr": "French",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "ht": "Haitian Creole",
    "he": "Hebrew",
    "hi": "Hindi",
    "mww": "Hmong Daw",
    "hu": "Hungarian",
    "is": "Icelandic",
    "id": "Indonesian",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "kk": "Kazakh",
    "sw": "Kiswahili",
    "tlh": "Klingon",
    "ko": "Korean",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "mg": "Malagasy",
    "ms": "Malay (Latin)",
    "ml": "Malayalam",
    "mt": "Maltese",
    "mi": "Maori",
    "mr": "Marathi",
    "nb": "Norwegian Bokmål",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese (Brazil)",
    "pt-pt": "Portuguese (Portugal)",
    "pa": "Punjabi (Gurmukhi)",
    "otq": "Querétaro Otomi",
    "ro": "Romanian",
    "ru": "Russian",
    "sm": "Samoan",
    "sr-Cyrl": "Serbian (Cyrillic)",
    "sr-Latn": "Serbian (Latin)",
    "sk": "Slovak",
    "sl": "Slovenian",
    "es": "Spanish",
    "sv": "Swedish",
    "ty": "Tahitian",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "to": "Tongan",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "cy": "Welsh",
    "yua": "Yucatec Maya",
    "auto-detect": "Auto Detect",
}
started = False
# Functions


def server_prefixes(id=None, prefix=None, mode="r"):
    if not os.path.isfile("core/prefixes.json"):
        with open("core/prefixes.json", "w") as f:
            f.write("{}\n")
    if mode == "r":
        return json.load(open("core/prefixes.json"))
    elif mode == "w":
        existing = json.load(open("core/prefixes.json"))
        existing[str(id)] = prefix
        with open("core/prefixes.json", mode="w") as f:
            json.dump(existing, f, indent=4)
        return existing


# Monkey patch discord
async def identify(self):
    """Sends the IDENTIFY packet."""
    payload = {
        "op": self.IDENTIFY,
        "d": {
            "token": self.token,
            "properties": {
                "$os": "Android",
                "$browser": "Discord Android",
                "$device": "Discord Android",
                "$referrer": "",
                "$referring_domain": "",
            },
            "compress": True,
            "large_threshold": 250,
            "guild_subscriptions": self._connection.guild_subscriptions,
            "v": 3,
        },
    }

    if not self._connection.is_bot:
        payload["d"]["synced_guilds"] = []

    if self.shard_id is not None and self.shard_count is not None:
        payload["d"]["shard"] = [self.shard_id, self.shard_count]

    state = self._connection
    if state._activity is not None or state._status is not None:
        payload["d"]["presence"] = {
            "status": state._status,
            "game": state._activity,
            "since": 0,
            "afk": False,
        }

    await self.send_as_json(payload)
    discord.gateway.log.info(
        "Shard ID %s has sent the IDENTIFY payload.", self.shard_id
    )


discord.gateway.DiscordWebSocket.identify = identify


# setup logging

if not os.path.isdir("logs"):
    os.mkdir("logs")
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
handler = logging.FileHandler(filename="logs/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)
logger = logging.getLogger("MechaDon")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
