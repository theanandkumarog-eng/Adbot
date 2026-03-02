import os
import asyncio
import random
import traceback
from typing import Dict, List

from telethon import TelegramClient, functions
from telethon.errors import (
    FloodWaitError,
    PeerFloodError,
    ChatWriteForbiddenError,
    AuthKeyUnregisteredError
)

from config import API_ID, API_HASH, SESSION_DIR
from Nexa.database.users import users_db
from Nexa.core.session_manager import list_user_sessions
from Nexa.core.logger import logger
from Nexa.core.broadcast_logs import send_log
from Nexa.core.profile_config import CUSTOM_LAST_NAME, CUSTOM_BIO


running_tasks: Dict[int, asyncio.Task] = {}
running_delays: Dict[int, int] = {}
clients: Dict[str, TelegramClient] = {}


# ==============================
# Utility: Safe Log
# ==============================
async def safe_log(user_id: int, text: str):
    try:
        await send_log(user_id, text)
    except Exception:
        pass


def set_user_delay(user_id: int, delay: int):
    running_delays[user_id] = delay


# ==============================
# Start Broadcast
# ==============================
async def start_broadcast(user_id: int) -> bool:
    if user_id in running_tasks and not running_tasks[user_id].done():
        return True

    user = await users_db.find_one({"_id": user_id})
    if not user:
        await safe_log(user_id, "⚠️ User not found.")
        return False

    if not user.get("advertising") or not user.get("ad_message"):
        await safe_log(user_id, "⚠️ No ad message or advertising disabled.")
        return False

    sessions = list_user_sessions(user_id)
    if not sessions:
        await safe_log(user_id, "⚠️ No accounts found for broadcast.")
        return False

    # Update profiles for all sessions
    await asyncio.gather(*[
        update_profile_for_session(user_id, s)
        for s in sessions
    ])

    # Set user delay
    running_delays[user_id] = int(user.get("delay", 300))
    task = asyncio.create_task(broadcast_loop(user_id))
    running_tasks[user_id] = task

    await safe_log(user_id, "🚀 <b>Broadcast started!</b>")
    return True


# ==============================
# Stop Broadcast
# ==============================
async def stop_broadcast(user_id: int):
    await users_db.update_one({"_id": user_id}, {"$set": {"advertising": False}})

    task = running_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()

    running_delays.pop(user_id, None)

    for key in list(clients.keys()):
        if key.startswith(f"{user_id}_"):
            try:
                await clients[key].disconnect()
            except Exception:
                pass
            clients.pop(key, None)

    await safe_log(user_id, "🛑 <b>Broadcast stopped</b>")


# ==============================
# Profile Update
# ==============================
async def update_profile_for_session(user_id: int, session_name: str):
    session_path = os.path.join(SESSION_DIR, f"{session_name}.session")
    if not os.path.exists(session_path):
        return

    session_base = session_path.replace(".session", "")
    client = TelegramClient(session_base, API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            return

        await client(functions.account.UpdateProfileRequest(
            last_name=CUSTOM_LAST_NAME,
            about=CUSTOM_BIO
        ))

        await safe_log(user_id, f"📝 Profile updated: {session_name}")

    except Exception:
        pass
    finally:
        await client.disconnect()


# ==============================
# Broadcast Loop
# ==============================
async def broadcast_loop(user_id: int):
    try:
        while True:
            user = await users_db.find_one({"_id": user_id})
            if not user or not user.get("advertising"):
                break

            message = (user.get("ad_message") or "").strip()
            if not message:
                await safe_log(user_id, "⚠️ No ad message found. Waiting...")
                await asyncio.sleep(10)
                continue

            sessions = list_user_sessions(user_id)
            if not sessions:
                await safe_log(user_id, "⚠️ No accounts found. Waiting...")
                await asyncio.sleep(10)
                continue

            await asyncio.gather(*[
                send_from_session(user_id, s, message)
                for s in sessions
            ])

            delay = running_delays.get(user_id, 300)
            await asyncio.sleep(delay)

    except asyncio.CancelledError:
        pass
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        running_tasks.pop(user_id, None)
        running_delays.pop(user_id, None)
        await safe_log(user_id, "🛑 <b>Broadcast ended</b>")


# ==============================
# Send From Session
# ==============================
async def send_from_session(
    user_id: int,
    session_name: str,
    message: str,
    target_ids: List[int] = None
):
    session_path = os.path.join(SESSION_DIR, f"{session_name}.session")
    if not os.path.exists(session_path):
        return

    session_base = session_path.replace(".session", "")
    key = f"{user_id}_{session_name}"

    try:
        if key not in clients:
            client = TelegramClient(session_base, API_ID, API_HASH)
            await client.connect()
            clients[key] = client
        else:
            client = clients[key]

        if not await client.is_user_authorized():
            await client.disconnect()
            clients.pop(key, None)
            return

        me = await client.get_me()
        phone = f"+{me.phone}" if me.phone else session_name

        # Determine chats to send to
        if target_ids:
            chats = []
            for chat_id in target_ids:
                try:
                    entity = await client.get_entity(chat_id)
                    chats.append(entity)
                except Exception:
                    continue
        else:
            dialogs = await client.get_dialogs(limit=None)
            chats = [d.entity for d in dialogs if d.is_group or d.is_channel]

        for chat in chats:
            try:
                await client.send_message(chat, message)

                # Update DB
                await users_db.update_one(
                    {"_id": user_id},
                    {"$inc": {"messages_sent": 1}}
                )

                chat_title = getattr(chat, "title", None) or getattr(chat, "first_name", "Unknown")
                chat_id = getattr(chat, "id", "Unknown")

                # ✅ Success log in UI style
                await safe_log(
                    user_id,
                    f"✅ Sent to {chat_title} (<code>{chat_id}</code>) using account {phone}"
                )

                await asyncio.sleep(random.randint(3, 6))

            except FloodWaitError as e:
                await safe_log(user_id, f"⏳ FloodWait {e.seconds}s for <code>{phone}</code>")
                await asyncio.sleep(e.seconds)

            except (PeerFloodError, ChatWriteForbiddenError, AuthKeyUnregisteredError):
                continue  # Skip blocked chats silently

            except Exception:
                continue  # Skip any other chat error

    except Exception:
        logger.error(traceback.format_exc())