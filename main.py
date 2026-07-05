import os
import time
import re
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest, UpdateProfileRequest
from telethon.tl.functions.contacts import BlockRequest

# --- CONFIG ---
API_ID = 30053888         
API_HASH = '942c4ac7a2398835b55ec1bf562ac028'

UZB_AWAY_MSG = "Salom! Hozir bandman yoki Telegramga kirmadim. Bildirishnomalarim (notification) o'chiq turibdi, xabarni ko'rishim bilan javob beraman!"
ENG_AWAY_MSG = "Hi, wsp! I am busy rn or haven't opened the Telegram app. My notifications are turned off, I'll reply when I see the message!"

UZB_SWEAR_WORDS = ["suka", "gandon", "qotoq", "jalap", "jalab", "am", "dalbayob", "skay", "sik", "sikaman", "haromi", "xaromi", "kot", "yban", "eban"]
# --------------

client = TelegramClient('my_permanent_session', API_ID, API_HASH)

last_reply_time = {}
user_word_spam_tracker = {}
view_once_cache = {}
last_bio_status = ""

def clean_and_normalize_text(text):
    if not text: return ""
    text = text.lower().strip()
    text = text.replace("0", "o").replace("3", "e").replace("4", "a").replace("1", "i")
    return re.sub(r'[^a-z\'\`\'指標’’а-яё]', '', text)

# 1. PREMIUM BIO STATUS (Native Background Loop)
async def bio_status_loop():
    global last_bio_status
    await client.wait_until_ready()
    while True:
        try:
            me_full = await client(GetFullUserRequest('me'))
            is_online = getattr(me_full.user.status, 'was_online', None) is None
            new_bio = "⚡ Cloud Engine: Active & Protected 24/7" if is_online else "🌙 Cloud Engine: Running (Offline Mode)"
            if new_bio != last_bio_status:
                await client(UpdateProfileRequest(about=new_bio))
                last_bio_status = new_bio
                print(f"⚙️ Bio Status Updated: {new_bio}")
        except Exception as e:
            print(f"Bio sync skip: {e}")
        await asyncio.sleep(300) # Checks and refreshes smoothly every 5 minutes

# 2. VIEW-ONCE UNLOCKER (Reply with .get)
@client.on(events.NewMessage(outgoing=True))
async def view_once_unlocker(event):
    if event.is_private and event.text and event.text.strip().lower() == '.get' and event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.id in view_once_cache:
            cached_path = view_once_cache[reply_msg.id]
            if os.path.exists(cached_path):
                await event.delete()
                await client.send_file(event.chat_id, cached_path, caption="🔓 **View-Once Photo Recovered Successfully!**")

# 3. SPY SYSTEMS (Deleted & Edited tracking)
@client.on(events.MessageDeleted)
async def deleted_handler(event):
    for msg_id in event.deleted_ids:
        message = await client.get_messages(event.chat_id, ids=msg_id)
        if message:
            sender = await message.get_sender()
            name = getattr(sender, 'first_name', 'Someone')
            if message.text:
                await client.send_message('me', f"🗑️ **DELETED**\n**From:** {name}\n**Text:** {message.text}")
            elif message.photo:
                await client.send_message('me', f"🗑️ **DELETED PHOTO**\n**From:** {name}")
                path = await message.download_media()
                await client.send_file('me', path)
                os.remove(path)

@client.on(events.MessageEdited)
async def edited_handler(event):
    if event.is_private and event.original_message.text:
        sender = await event.get_sender()
        name = getattr(sender, 'first_name', 'Someone')
        await client.send_message('me', f"✏️ **EDITED**\n**From:** {name}\n**Old:** {event.original_message.text}\n**New:** {event.text}")

# 4. GHOST READ + AUDIO TRANSCRIPTION TAG
@client.on(events.NewMessage(incoming=True))
async def ghost_read_handler(event):
    if event.is_private:
        my_id = (await client.get_me()).id
        if event.chat_id == my_id or event.sender_id == my_id: return
        if event.text and any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS): return

        sender = await event.get_sender()
        name = getattr(sender, 'first_name', 'Someone')
        
        if event.text and not event.photo and not event.voice and not event.video_note:
            await client.send_message('me', f"👁️ **GHOST READ**\n**From:** {name}\n**Message:** {event.text}")
        elif event.photo or event.voice or event.video_note:
            media_type = "Photo" if event.photo else ("Voice Note" if event.voice else "Video Message")
            log = f"👁️ **GHOST READ MEDIA**\n**From:** {name}\n**Type:** {media_type}"
            if event.voice:
                log += "\n📝 **Premium Transcription:** _[Audio processing active... Click file to listen]_"
            await client.send_message('me', log)
            temp_media = await event.download_media()
            if event.photo: view_once_cache[event.id] = temp_media
            await client.send_file('me', temp_media)
            if not event.photo and os.path.exists(temp_media): os.remove(temp_media)

# 5. AUTO RESPONDER
@client.on(events.NewMessage(incoming=True))
async def offline_auto_responder(event):
    if event.is_private:
        current_time = time.time()
        if event.chat_id in last_reply_time and (current_time - last_reply_time[event.chat_id]) < 300: return
        if event.text and any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS): return
        try:
            me = await client(GetFullUserRequest('me'))
            if getattr(me.user.status, 'was_online', None) is None: return
        except Exception: pass

        last_reply_time[event.chat_id] = current_time
        await event.reply(f"🇺🇿 UZ:\n{UZB_AWAY_MSG}\n\n🇬🇧 EN:\n{ENG_AWAY_MSG}")

# 6. SPAM & DETAILED SWEAR BLOCKER
@client.on(events.NewMessage(incoming=True))
async def spam_and_swear_blocker_handler(event):
    if event.is_private and event.text:
        current_time = time.time()
        sender_id = event.sender_id
        cleaned_text = event.text.strip().lower()
        sender = await event.get_sender()
        first_name = getattr(sender, 'first_name', 'Unknown')
        username = getattr(sender, 'username', 'None')
        mention = f"@{username}" if username != 'None' else "No Username"
        
        if any(swear in clean_and_normalize_text(event.text) for swear in UZB_SWEAR_WORDS):
            try:
                await event.delete() 
                await client(BlockRequest(id=sender_id)) 
                await client.send_message('me', f"🔒 **TOXIC USER BANNED**\n👤 **Name:** {first_name}\n🆔 **ID:** `{sender_id}`\n🌐 **User:** {mention}\n💬 **Text:** ||{event.text}||")
            except Exception: pass
            return

        if sender_id not in user_word_spam_tracker:
            user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}
        else:
            history = user_word_spam_tracker[sender_id]
            if history["text"] == cleaned_text and (current_time - history["timestamp"]) < 180:
                history["count"] += 1
                history["timestamp"] = current_time
                if 3 <= history["count"] < 5: await event.delete()
                elif history["count"] >= 5:
                    await event.delete()
                    try:
                        await client(BlockRequest(id=sender_id))
                        await client.send_message('me', f"🔒 **SPAMMER BANNED**\n👤 **Name:** {first_name}\n🆔 **ID:** `{sender_id}`\n🌐 **User:** {mention}\n📝 **Text:** \"{event.text}\"")
                    except Exception: pass
            else:
                user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}
                
    elif event.is_group or event.is_channel:
        await client.send_read_acknowledge(event.chat_id, max_id=event.id)

print("🚀 Cloud Engine Active!")
client.start()
# Fire up the parallel background task for bio adjustments
client.loop.create_task(bio_status_loop())
client.run_until_disconnected()
