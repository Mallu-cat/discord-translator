import os
import discord
import requests
from langdetect import detect, LangDetectException

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Change this if you want a different target language
TARGET_LANG = os.getenv("TARGET_LANG", "en")

# Free public endpoint (can be rate-limited sometimes)
TRANSLATE_URL = os.getenv("TRANSLATE_URL", "https://translate.argosopentech.com/translate")

intents = discord.Intents.default()
intents.message_content = True  # REQUIRED
client = discord.Client(intents=intents)

def translate_text(text: str, target: str) -> str | None:
    try:
        data = {
            "q": text,
            "source": "auto",
            "target": target,
            "format": "text",
        }
        r = requests.post(TRANSLATE_URL, data=data, timeout=15)
        r.raise_for_status()
        out = r.json().get("translatedText", "")
        return out.strip() or None
    except Exception:
        return None

@client.event
async def on_ready():
    print(f"✅ Logged in as: {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not message.content:
        return

    # Avoid translating commands if you use them
    if message.content.startswith(("!", "/", ".")):
        return

    # Detect language
    try:
        lang = detect(message.content)
    except LangDetectException:
        return

    # If already in target language, do nothing
    if lang == TARGET_LANG:
        return

    translated = translate_text(message.content, TARGET_LANG)
    if not translated:
        return

    # Avoid replying with identical text
    if translated.lower().strip() == message.content.lower().strip():
        return

    await message.reply(f"{TARGET_LANG.upper()}: {translated}", mention_author=False)

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to Render Environment Variables.")

client.run(DISCORD_TOKEN)
