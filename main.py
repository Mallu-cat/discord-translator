import os
import discord
import aiohttp
from langdetect import detect

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# LibreTranslate public instance (can rate-limit; you can switch instances later)
LIBRE_URL = os.getenv("LIBRE_URL", "https://translate.argosopentech.com/translate")

# Auto-translate: if message is NOT English, reply with EN translation
AUTO_TO_EN = True

intents = discord.Intents.default()
intents.message_content = True # MUST be enabled in Dev Portal too
client = discord.Client(intents=intents)


async def libre_translate(session: aiohttp.ClientSession, text: str, target: str) -> str:
    payload = {
        "q": text,
        "source": "auto",
        "target": target,
        "format": "text",
    }
    async with session.post(LIBRE_URL, data=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        if resp.status != 200:
            body = await resp.text()
            raise RuntimeError(f"Translate API error {resp.status}: {body[:200]}")
        data = await resp.json()
        return data.get("translatedText", "").strip()


def looks_like_lang_code(s: str) -> bool:
    s = s.strip().lower()
    return s in {"en", "de", "tr", "pl", "ja", "ko", "ar"}


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not message.content:
        return

    content = message.content.strip()

    # --- A) Reply-translate mode ---
    # If user replies to a message and sends "DE" / "TR" / etc, translate replied message.
    if message.reference and looks_like_lang_code(content):
        try:
            replied = await message.channel.fetch_message(message.reference.message_id)
            if not replied.content:
                return
            async with aiohttp.ClientSession() as session:
                translated = await libre_translate(session, replied.content, content.lower())
            if translated:
                await message.reply(f"**{content.upper()}**: {translated}", mention_author=False)
        except Exception as e:
            await message.reply(f"❌ Translate failed: {e}", mention_author=False)
        return

    # --- B) Command mode ---
    # tr <lang> <text>
    # Example: "tr de hello" or reply to a message with "tr de"
    if content.lower().startswith("tr "):
        parts = content.split(maxsplit=2) # ["tr", "de", "text..."]
        if len(parts) < 2:
            await message.reply("Use: `tr <lang> <text>` OR reply to a message with `tr <lang>`", mention_author=False)
            return

        target = parts[1].lower()
        text = parts[2] if len(parts) >= 3 else ""

        # If no text provided, try to translate the replied-to message
        if not text and message.reference:
            try:
                replied = await message.channel.fetch_message(message.reference.message_id)
                text = replied.content or ""
            except:
                text = ""

        if not text:
            await message.reply("Nothing to translate. Use: `tr <lang> <text>`", mention_author=False)
            return

        try:
            async with aiohttp.ClientSession() as session:
                translated = await libre_translate(session, text, target)
            if translated:
                await message.reply(f"**{target.upper()}**: {translated}", mention_author=False)
        except Exception as e:
            await message.reply(f"❌ Translate failed: {e}", mention_author=False)
        return

    # --- C) Auto mode: non-English -> English ---
    if AUTO_TO_EN:
        try:
            lang = detect(content)
        except:
            return

        if lang != "en":
            try:
                async with aiohttp.ClientSession() as session:
                    translated = await libre_translate(session, content, "en")
                if translated and translated.lower() != content.lower():
                    await message.reply(f"**EN**: {translated}", mention_author=False)
            except Exception as e:
                # don't spam channel; just log
                print("Translate error:", e)


if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN env var")

client.run(DISCORD_TOKEN)
