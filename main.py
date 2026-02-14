import discord
import os
from langdetect import detect, DetectorFactory
import requests

DetectorFactory.seed = 0

TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_LANG = "en"
TRANSLATE_URL = "https://translate.argosopentech.com/translate"

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True          # IMPORTANT: receive message events
intents.message_content = True   # IMPORTANT: read message text
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
    # Debug: prove we received a message (shows in Render logs)
    print("GOT MESSAGE:", message.guild, "#"+getattr(message.channel, "name", "DM"), message.author, repr(message.content))

    if message.author.bot or not message.content:
        return

    text = message.content.strip()

    # Skip commands
    if text.startswith(("/", "!", ".", "?")):
        return

    # Skip very short messages (langdetect often mislabels them as English)
    if len(text) < 6:
        print("SKIP: too short for reliable detection")
        return

    try:
        lang = detect(text)
        print("DETECTED LANG:", lang)
    except Exception as e:
        print("DETECT ERROR:", e)
        return

    # Skip if already English
    if lang == "en":
        print("SKIP: detected English")
        return

    try:
        translated = translate(text, "en")
        print("TRANSLATED:", translated)
    except Exception as e:
        print("TRANSLATE ERROR:", e)
        return

    if not translated:
        return

    if translated.lower() != text.lower():
        await message.reply(f"EN: {translated}", mention_author=False)


client.run(TOKEN)
