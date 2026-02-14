import discord
import os
from langdetect import detect
from googletrans import Translator

TOKEN = os.getenv("DISCORD_TOKEN")

translator = Translator()

# Enable message content intent
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    text = message.content.strip()

    if not text:
        return

    print("Received message:", text)

    try:
        lang = detect(text)
    except:
        return

    # Only translate if NOT English
    if lang == "en":
        return

    try:
        translated = translator.translate(text, dest="en").text
        await message.reply(f"EN: {translated}", mention_author=False)
    except Exception as e:
        print("Translation error:", e)

client.run(TOKEN)
