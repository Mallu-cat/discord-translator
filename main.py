import os
import discord
import requests
from langdetect import detect, LangDetectException

TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_LANG = "en"

# Discord intents (you must also enable Message Content Intent in Dev Portal)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def translate_text(text: str, target: str = "en") -> str:
    url = "https://translate.argosopentech.com/translate"
    data = {
        "q": text,
        "source": "auto",
        "target": target,
        "format": "text"
    }
    r = requests.post(url, data=data, timeout=20)
    r.raise_for_status()
    return r.json().get("translatedText", "")

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    # ignore other bots (including itself)
    if message.author.bot:
        return

    text = (message.content or "").strip()
    if not text:
        return

    # ignore commands to avoid spam
    if text.startswith(("/", "!", ".", "?")):
        return

    print("GOT MESSAGE:", message.author, repr(text))

    # language detect
    try:
        lang = detect(text)
    except LangDetectException:
        print("SKIP: language detect failed")
        return

    print("DETECTED:", lang)

    # don't translate English
    if lang == TARGET_LANG:
        return

    # translate
    try:
        translated = translate_text(text, TARGET_LANG)
    except Exception as e:
        print("TRANSLATE ERROR:", e)
        return

    if translated and translated.lower() != text.lower():
        await message.reply(f"EN: {translated}", mention_author=False)

client.run(TOKEN)
