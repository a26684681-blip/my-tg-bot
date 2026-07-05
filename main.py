import os
import time
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.contacts import BlockRequest

# --- CONFIGURATION (YOUR SECURE KEYS ARE SAVED) ---
API_ID = 30053888         
API_HASH = '942c4ac7a2398835b55ec1bf562ac028'

UZB_AWAY_MSG = "Salom! Hozir bandman yoki Telegramga kirmadim. Bildirishnomalarim (notification) o'chiq turibdi, xabarni ko'rishim bilan javob beraman!"
ENG_AWAY_MSG = "Hi, wsp! I am busy rn or haven't opened the Telegram app. My notifications are turned off, I'll reply when I see the message!"
# --------------------------------------------------------

client = TelegramClient('my_permanent_session', API_ID, API_HASH)

last_reply_time = {}
# Dictionary to strictly track exact word repetition for blocking
user_word_spam_tracker = {}

# FEATURE 1 & 5: Catch Deleted and Edited Messages/Photos
@client.on(events.MessageDeleted)
async def deleted_handler(event):
    for msg_id in event.deleted_ids:
        message = await client.get_messages(event.chat_id, ids=msg_id)
        if message:
            sender = await message.get_sender()
            name = getattr(sender, 'first_name', 'Someone')
            alert = f"🗑️ **DELETED MESSAGE CAPTURED**\n**From:** {name}\n"
            if message.text:
                alert += f"**Text:** {message.text}"
                await client.send_message('me', alert)
            elif message.photo:
                alert += "**Type:** Private Photo (Saved below)"
                await client.send_message('me', alert)
                path = await message.download_media()
                await client.send_file('me', path)
                os.remove(path)

@client.on(events.MessageEdited)
async def edited_handler(event):
    if event.is_private and event.original_message.text:
        sender = await event.get_sender()
        name = getattr(sender, 'first_name', 'Someone')
        alert = f"✏️ **EDITED MESSAGE SPY**\n**From:** {name}\n**Original Text:** {event.original_message.text}\n**New Text:** {event.text}"
        await client.send_message('me', alert)

# FEATURE 8: Ultimate Ghost Read Mode (Saves Media Infinitely to Saved Messages)
@client.on(events.NewMessage(incoming=True))
async def ghost_read_handler(event):
    if event.is_private:
        my_id = (await client.get_me()).id
        if event.chat_id == my_id or event.sender_id == my_id:
            return
            
        sender = await event.get_sender()
        name = getattr(sender, 'first_name', 'Someone')
        
        if event.text and not event.photo and not event.voice and not event.video_note:
            ghost_log = f"👁️ **GHOST READ (UNREAD)**\n**From:** {name}\n**Message:** {event.text}"
            await client.send_message('me', ghost_log)
            
        elif event.photo or event.voice or event.video_note:
            media_type = "Photo (Could be View-Once)" if event.photo else ("Voice Note" if event.voice else "Video Message")
            ghost_log = f"👁️ **GHOST READ MEDIA (UNREAD)**\n**From:** {name}\n**Type:** {media_type}"
            await client.send_message('me', ghost_log)
            
            temp_media = await event.download_media()
            await client.send_file('me', temp_media)
            os.remove(temp_media)

# FEATURE 2, 3 & 6: Smart Auto-Reply (STRICT OFFLINE ONLY SENSOR)
@client.on(events.NewMessage(incoming=True))
async def offline_auto_responder(event):
    if event.is_private:
        current_time = time.time()
        chat_id = event.chat_id
        
        if chat_id in last_reply_time and (current_time - last_reply_time[chat_id]) < 300:
            return

        try:
            me = await client(GetFullUserRequest('me'))
            is_online = getattr(me.user.status, 'was_online', None) is None
            if is_online:
                return
        except Exception:
            pass

        last_reply_time[chat_id] = current_time
        
        if event.photo:
            await event.reply("Rasm qabul qilindi! / Photo received!")
        elif event.voice:
            await event.reply("Ovozli xabar qabul qilindi! / Voice note received!")
        elif event.video_note:
            await event.reply("Video xabar qabul qilindi! / Video message received!")

        await event.reply(f"🇺🇿 UZ:\n{UZB_AWAY_MSG}\n\n🇬🇧 EN:\n{ENG_AWAY_MSG}")

# FEATURE 9: Exact Word 5-Times Repeating Auto-Blocker (No Scam Link Check)
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
            
            # Checks if they are sending the EXACT same text within a 3-minute window
            if history["text"] == cleaned_text and (current_time - history["timestamp"]) < 180:
                history["count"] += 1
                history["timestamp"] = current_time # update to latest text time
                
                # If they send the exact same message 3 or 4 times, delete it to keep chat clean
                if history["count"] >= 3 and history["count"] < 5:
                    print(f"🗑️ Anti-Spam: Vaporized repeated spam text.")
                    await event.delete()
                
                # 🔥 STRIKE 5: Automatically BLOCKS the user from your account!
                elif history["count"] >= 5:
                    print(f"🚫 Anti-Spam Security: Automatically blocking user ID {sender_id} for spamming.")
                    await event.delete() # Wipe the 5th message
                    try:
                        await client(BlockRequest(id=sender_id)) # Fire the block request to Telegram
                        await client.send_message('me', f"🔒 **USER BLOCKED AUTOMATICALLY**\nAn account was just blocked for sending the exact same phrase 5 times rapidly.")
                    except Exception as e:
                        print(f"Failed to block user: {e}")
                    return
            else:
                # Reset if they type a different word or if 3 minutes have passed safely
                user_word_spam_tracker[sender_id] = {"text": cleaned_text, "timestamp": current_time, "count": 1}
                
    elif event.is_group or event.is_channel:
        await client.send_read_acknowledge(event.chat_id, max_id=event.id)

print("🚀 ALL SYSTEMS ONLINE: Cleaned Auto-Block Engine is live!")
client.start()
client.run_until_disconnected()


