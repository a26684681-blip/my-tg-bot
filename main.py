import os
import time
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.contacts import BlockRequest

# --- CONFIGURATION (YOUR WORKING KEYS) ---
API_ID = 30053888         
API_HASH = '942c4ac7a2398835b55ec1bf562ac028'

UZB_AWAY_MSG = "Salom! Hozir bandman yoki Telegramga kirmadim. Bildirishnomalarim (notification) o'chiq turibdi, xabarni ko'rishim bilan javob beraman!"
ENG_AWAY_MSG = "Hi, wsp! I am busy rn or haven't opened the Telegram app. My notifications are turned off, I'll reply when I see the message!"
# --------------------------------------------------------

# Clean new session profile name to bypass the AuthKeyDuplicatedError
client = TelegramClient('fresh_cloud_engine_session', API_ID, API_HASH)

last_reply_time = {}
user_word_spam_tracker = {}

# FEATURE 1: Capture Deleted Chats
@client.on(events.MessageDeleted)
async def deleted_handler(event):
    for msg_id in event.deleted_ids:
        message = await client.get_messages(event.chat_id, ids=msg_id)
        if message:
            sender = await message.get_sender()
            name = getattr(sender, 'first_name', 'Someone')
            if message.text:
                await client.send_message('me', f"🗑️ **DELETED**\n**From:** {name}\n**Text:** {message.text}")

# FEATURE 2: Silent High-Speed Media Backups to Saved Messages
@client.on(events.NewMessage(incoming=True))
async def ghost_read_handler(event):
    if event.is_private:
        my_id = (await client.get_me()).id
        if event.chat_id == my_id or event.sender_id == my_id: return
        
        sender = await event.get_sender()
        name = getattr(sender, 'first_name', 'Someone')
        
        if event.text and not event.photo and not event.voice:
            await client.send_message('me', f"👁️ **GHOST READ**\n**From:** {name}\n**Message:** {event.text}")
        elif event.photo or event.voice:
            temp = await event.download_media()
            await client.send_file('me', temp, caption=f"👁️ **GHOST MEDIA**\n**From:** {name}")
            os.remove(temp)

# FEATURE 3: Smart Offline-Only Auto Responder
@client.on(events.NewMessage(incoming=True))
async def offline_auto_responder(event):
    if event.is_private:
        current_time = time.time()
        if event.chat_id in last_reply_time and (current_time - last_reply_time[event.chat_id]) < 300: return
        try:
            me = await client(GetFullUserRequest('me'))
            if getattr(me.user.status, 'was_online', None) is None: return
        except Exception: pass

        last_reply_time[event.chat_id] = current_time
        await event.reply(f"🇺🇿 UZ:\n{UZB_AWAY_MSG}\n\n🇬🇧 EN:\n{ENG_AWAY_MSG}")

# FEATURE 4: 5-Times Repeating Word Spam Blocker
@client.on(events.NewMessage(incoming=True))
async def spam_blocker_handler(event):
    if event.is_private and event.text:
        current_time = time.time()
        sender_id = event.sender_id
        cleaned_text = event.text.strip().lower()
        
        if sender_id not in user_word_spam_tracker:
            user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}
        else:
            history = user_word_spam_tracker[sender_id]
            if history["text"] == cleaned_text and (current_time - history["timestamp"]) < 180:
                history["count"] += 1
                history["timestamp"] = current_time
                if history["count"] >= 3: await event.delete()
                if history["count"] >= 5:
                    try: await client(BlockRequest(id=sender_id))
                    except Exception: pass
            else:
                user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}

print("🚀 Cloud Engine Restored!")
client.start()
client.run_until_disconnected()
