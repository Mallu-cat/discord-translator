print("=== Translator Bot START (deep-translator build) ===", flush=True)

import os
import discord
from langdetect import detect
from deep_translator import GoogleTranslator

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

AUTO_TO_EN = True

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.dm_messages = True

client = discord.Client(intents=intents)


def safe_translate(text: str, target: str) -> str:
    # GoogleTranslator supports many language codes like "en", "de", "et", "ru", etc.
    return GoogleTranslator(source="auto", target=target).translate(text) or ""


def looks_like_lang_code(s: str) -> bool:
    s = s.strip().lower()
    # Expand as needed
    return s in {"en", "de", "et", "ru", "fi", "sv", "pl", "tr", "es", "fr", "it", "pt", "nl", "ja", "ko", "ar"}


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} ({client.user.id})", flush=True)


@client.event
async def on_message(message: discord.Message):
    # Log every message event we receive
    try:
        author = f"{message.author} ({message.author.id})"
        channel = f"{getattr(message.channel, 'name', 'DM')} ({message.channel.id})"
        guild = "DM" if message.guild is None else str(message.guild.id)
        content_len = 0 if message.content is None else len(message.content)
        print(
            f"[on_message] guild={guild} channel={channel} author={author} "
            f"is_bot={message.author.bot} content_len={content_len}",
            flush=True
        )
    except Exception as e:
        print("[on_message] logging failed:", repr(e), flush=True)

    if message.author.bot:
        return

    content = (message.content or "").strip()

    # ping test
    if content.lower() == "ping":
        try:
            await message.reply("pong ✅", mention_author=False)
        except Exception as e:
            print("[reply failed on ping]:", repr(e), flush=True)
        return

    if not content:
        return

    # A) Reply-translate mode: reply to a message with just "de" / "en" / etc
    if message.reference and looks_like_lang_code(content):
        try:
            replied = await message.channel.fetch_message(message.reference.message_id)
            text = (replied.content or "").strip()
            if not text:
                return
            translated = safe_translate(text, content.lower()).strip()
            if translated:
                await message.reply(f"**{content.upper()}**: {translated}", mention_author=False)
        except Exception as e:
            print("[reply-translate failed]:", repr(e), flush=True)
            try:
                await message.reply(f"❌ Translate failed: {e}", mention_author=False)
            except Exception as e2:
                print("[failed to send error reply]:", repr(e2), flush=True)
        return

    # B) Command mode: tr <lang> <text> (or reply with "tr <lang>")
    if content.lower().startswith("tr "):
        parts = content.split(maxsplit=2)
        if len(parts) < 2:
            try:
                await message.reply(
                    "Use: `tr <lang> <text>` OR reply to a message with `tr <lang>`",
                    mention_author=False,
                )
            except Exception as e:
                print("[failed to send usage reply]:", repr(e), flush=True)
            return

        target = parts[1].lower()
        text = parts[2] if len(parts) >= 3 else ""

        if not text and message.reference:
            try:
                replied = await message.channel.fetch_message(message.reference.message_id)
                text = (replied.content or "").strip()
            except Exception as e:
                print("[failed to fetch replied message]:", repr(e), flush=True)
                text = ""

        if not text:
            try:
                await message.reply("Nothing to translate. Use: `tr <lang> <text>`", mention_author=False)
            except Exception as e:
                print("[failed to send nothing-to-translate reply]:", repr(e), flush=True)
            return

        try:
            translated = safe_translate(text, target).strip()
            if translated:
                await message.reply(f"**{target.upper()}**: {translated}", mention_author=False)
        except Exception as e:
            print("[command translate failed]:", repr(e), flush=True)
            try:
                await message.reply(f"❌ Translate failed: {e}", mention_author=False)
            except Exception as e2:
                print("[failed to send error reply]:", repr(e2), flush=True)
        return

    # C) Auto mode: non-English -> English
    if AUTO_TO_EN:
        try:
            lang = detect(content)
        except Exception as e:
            print("[langdetect failed]:", repr(e), flush=True)
            return

        if lang != "en":
            try:
                translated = safe_translate(content, "en").strip()
                if translated and translated.lower() != content.lower():
                    await message.reply(f"**EN**: {translated}", mention_author=False)
            except Exception as e:
                print("[auto translate error]:", repr(e), flush=True)


if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN env var")

client.run(DISCORD_TOKEN)
