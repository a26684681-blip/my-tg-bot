import os
import time
import re
from telethon import TelegramClient, events

# --- CONFIGURATION ---
API_ID = 30053888         
API_HASH = '942c4ac7a2398835b55ec1bf562ac028'

# 🔑 PASTE YOUR BOT TOKEN FROM BOTFATHER BETWEEN THE QUOTES BELOW:
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

UZB_AWAY_MSG = "Salom! Men rasmiy avtomatlashtirilgan botman. Hozir admin yo'q yoki xabarlarni ko'ra olmaydi. Tez orada sizga javob qaytaramiz!"
ENG_AWAY_MSG = "Hello! I am an official automated assistant bot. The admin is currently busy or offline. We will reply to your message as soon as possible!"

UZB_SWEAR_WORDS = ["suka", "gandon", "qotoq", "jalap", "jalab", "am", "dalbayob", "skay", "sik", "sikaman", "haromi", "xaromi", "kot", "yban", "eban"]
# ---------------------

client = TelegramClient('bot_cloud_session', API_ID, API_HASH)

last_reply_time = {}
user_word_spam_tracker = {}

def clean_and_normalize_text(text):
    if not text: return ""
    text = text.lower().strip()
    text = text.replace("0", "o").replace("3", "e").replace("4", "a").replace("1", "i")
    return re.sub(r'[^a-z\'\`а-яё]', '', text)

@client.on(events.NewMessage(incoming=True))
async def bot_auto_responder(event):
    if event.is_private:
        current_time = time.time()
        chat_id = event.chat_id
        
        if chat_id in last_reply_time and (current_time - last_reply_time[chat_id]) < 300: return
        if event.text and any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS): return

        last_reply_time[chat_id] = current_time
        await event.reply(f"🇺🇿 UZ:\n{UZB_AWAY_MSG}\n\n🇬🇧 EN:\n{ENG_AWAY_MSG}")

@client.on(events.NewMessage(incoming=True))
async def spam_and_swear_blocker_handler(event):
    if event.is_private and event.text:
        current_time = time.time()
        sender_id = event.sender_id
        cleaned_text = event.text.strip().lower()
        
        if any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS):
            try: await event.delete()
            except Exception: pass
            return

        if sender_id not in user_word_spam_tracker:
            user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}
        else:
            history = user_word_spam_tracker[sender_id]
            if history["text"] == cleaned_text and (current_time - history["timestamp"]) < 180:
                history["count"] += 1
                history["timestamp"] = current_time
                if history["count"] >= 3:
                    try: await event.delete()
                    except Exception: pass
            else:
                user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}

print("🚀 Bot Engine Initializing...")
client.start(bot_token=BOT_TOKEN)
print("🎯 Cloud Bot Shield is officially locked green online 24/7!")
client.run_until_disconnected()
