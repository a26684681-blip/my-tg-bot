import os
import time
import re
from telethon import TelegramClient, events
from telethon.tl.functions.contacts import BlockRequest

# --- CONFIGURATION (YOUR SECURE SECRETS) ---
API_ID = 30053888         
API_HASH = '942c4ac7a2398835b55ec1bf562ac028'

# 🔑 PASTE YOUR BOT TOKEN FROM BOTFATHER BETWEEN THE QUOTES BELOW:
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

UZB_AWAY_MSG = "Salom! Men rasmiy avtomatlashtirilgan botman. Hozir admin yo'q yoki xabarlarni ko'ra olmaydi. Tez orada sizga javob qaytaramiz!"
ENG_AWAY_MSG = "Hello! I am an official automated assistant bot. The admin is currently busy or offline. We will reply to your message as soon as possible!"

UZB_SWEAR_WORDS = ["suka", "gandon", "qotoq", "jalap", "jalab", "am", "dalbayob", "skay", "sik", "sikaman", "haromi", "xaromi", "kot", "yban", "eban"]
# --------------------------------------------------------

# Initialize clean bot session structure
client = TelegramClient('bot_cloud_session', API_ID, API_HASH)

last_reply_time = {}
user_word_spam_tracker = {}

def clean_and_normalize_text(text):
    if not text: return ""
    text = text.lower().strip()
    text = text.replace("0", "o").replace("3", "e").replace("4", "a").replace("1", "i")
    return re.sub(r'[^a-z\'\`\'‘’а-яё]', '', text)

# FEATURE 1: Automatic Chat Greeting Message
@client.on(events.NewMessage(incoming=True))
async def bot_auto_responder(event):
    if event.is_private:
        current_time = time.time()
        chat_id = event.chat_id
        
        # Avoid flooding replies within a 5-minute window
        if chat_id in last_reply_time and (current_time - last_reply_time[chat_id]) < 300: 
            return

        # Skip replying if they sent a banned word
        if event.text and any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS): 
            return

        last_reply_time[chat_id] = current_time
        
        # Custom file notifications
        if event.photo:
            await event.reply("Rasm qabul qilindi! / Photo received!")
        elif event.voice:
            await event.reply("Ovozli xabar qabul qilindi! / Voice note received!")

        await event.reply(f"🇺🇿 UZ:\n{UZB_AWAY_MSG}\n\n🇬🇧 EN:\n{ENG_AWAY_MSG}")

# FEATURE 2: Strict Trick-Proof Profanity Blocker & Anti-Spam Security
@client.on(events.NewMessage(incoming=True))
async def spam_and_swear_blocker_handler(event):
    if event.is_private and event.text:
        current_time = time.time()
        sender_id = event.sender_id
        cleaned_text = event.text.strip().lower()
        
        # Grab profile credentials
        sender = await event.get_sender()
        first_name = getattr(sender, 'first_name', 'User')
        username = getattr(sender, 'username', 'None')
        mention = f"@{username}" if username != 'None' else "No Username"
        
        # 🚨 1. Profanity Detection Block
        if any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS):
            try:
                await event.delete() # Clear text instantly
                await client(BlockRequest(id=sender_id)) # Permanently ban from bot
                print(f"🔒 Banned toxic profile: {first_name} ({sender_id})")
            except Exception: pass
            return

        # 🛑 2. 5-Times Phrase Repetition Spam Block
        if sender_id not in user_word_spam_tracker:
            user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}
        else:
            history = user_word_spam_tracker[sender_id]
            if history["text"] == cleaned_text and (current_time - history["timestamp"]) < 180:
                history["count"] += 1
                history["timestamp"] = current_time
                if 3 <= history["count"] < 5: 
                    await event.delete()
                elif history["count"] >= 5:
                    await event.delete()
                    try:
                        await client(BlockRequest(id=sender_id))
                        print(f"🔒 Banned spammer profile: {first_name} ({sender_id})")
                    except Exception: pass
            else:
                user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}

print("🚀 Bot Engine Initializing...")
# Launch using direct official secure token logic
client.start(bot_token=BOT_TOKEN)
print("🎯 Cloud Bot Shield is officially locked green online 24/7!")
client.run_until_disconnected()
