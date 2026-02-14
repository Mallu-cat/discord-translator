import discord
import os
from langdetect import detect, DetectorFactory
import requests

DetectorFactory.seed = 0

TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_LANG = "en"
TRANSLATE_URL = "https://translate.argosopentech.com/translate"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def translate(text, target="en"):
    data = {
        "q": text,
        "source": "auto",
        "target": target,
        "format": "text"
    }
    response = requests.post(TRANSLATE_URL, data=data, timeout=15)
    response.raise_for_status()
    return response.json().get("translatedText", "")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot or not message.content:
        return

    text = message.content.strip()

    # Skip commands
    if text.startswith(("/", "!", ".", "?")):
        return

    try:
        lang = detect(text)
    except:
        return

    # Skip if already English
    if lang == TARGET_LANG:
        return

    try:
        translated = translate(text, TARGET_LANG)
    except Exception as e:
        print("Translation error:", e)
        return

    if not translated:
        return

    if translated.lower() != text.lower():
        await message.reply(f"EN: {translated}", mention_author=False)

client.run(TOKEN)
