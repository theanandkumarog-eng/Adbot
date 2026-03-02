# Nexa/plugins/start_broadcast.py

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import PeerIdInvalid

from Nexa.bot import bot
from Nexa.database.users import users_db
from Nexa.core.broadcast_engine import start_broadcast, running_tasks
from Nexa.core.broadcast_logs import init_logger, logger_bot

LOGGER_BOT_USERNAME = "AdxersLogsBot"


# ==================================================
# LOGGER CHECK
# ==================================================
async def is_logger_started(user_id: int) -> bool:
    """
    Ensures logger bot is started and checks if user exists.
    """
    try:
        await init_logger()
        await logger_bot.get_users(user_id)
        return True
    except PeerIdInvalid:
        return False
    except Exception:
        return False


# ==================================================
# START BROADCAST CALLBACK
# ==================================================
@bot.on_callback_query(filters.regex("^start_broadcast$"))
async def start_broadcast_callback(client, query):
    user_id = query.from_user.id
    user = await users_db.find_one({"_id": user_id})

    if not user:
        return await query.answer("User not found ❌", show_alert=True)

    # ==================================================
    # 1️⃣ CHECK ACCOUNTS
    # ==================================================
    if not user.get("accounts"):
        return await query.answer(
            "No account hosted yet ❌",
            show_alert=True
        )

    # ==================================================
    # 2️⃣ CHECK AD MESSAGE
    # ==================================================
    if not user.get("ad_message"):
        return await query.answer(
            "Set ad message first ❌",
            show_alert=True
        )

    # ==================================================
    # 3️⃣ LOGGER CHECK (ONLY ONCE)
    # ==================================================
    if not user.get("logger_verified"):
        if not await is_logger_started(user_id):
            return await query.message.edit_text(
                "⚠️ <b>Logger Bot Not Started</b>\n\n"
                f"Please start @{LOGGER_BOT_USERNAME} to receive logs.\n\n"
                "After starting, press Start Ads again.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "Start Logger Bot 📩",
                            url=f"https://t.me/{LOGGER_BOT_USERNAME}?start=verify"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅ Back",
                            callback_data="dashboard"
                        )
                    ]
                ])
            )

        # Mark verified permanently
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {"logger_verified": True}}
        )

    # ==================================================
    # 4️⃣ REAL RUNNING CHECK (ANTI-GHOST FIX)
    # ==================================================
    task = running_tasks.get(user_id)

    # If task exists but finished → cleanup
    if task and task.done():
        running_tasks.pop(user_id, None)
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {"advertising": False}}
        )
        task = None

    # If task exists but DB says advertising is False → cancel ghost task
    if task and not user.get("advertising"):
        task.cancel()
        running_tasks.pop(user_id, None)
        task = None

    # If still actively running → block
    if task and not task.done():
        return await query.answer(
            "Broadcast already running 🚀",
            show_alert=True
        )

    # If DB says advertising but no task → reset DB
    if user.get("advertising") and not task:
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {"advertising": False}}
        )

    # ==================================================
    # 5️⃣ ENABLE BROADCAST
    # ==================================================
    await users_db.update_one(
        {"_id": user_id},
        {"$set": {"advertising": True}}
    )

    started = await start_broadcast(user_id)

    # Failed to start → rollback
    if not started:
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {"advertising": False}}
        )
        return await query.answer(
            "Failed to start broadcast ❌",
            show_alert=True
        )

    # Success
    await query.answer("🚀 Broadcast Started")

    await query.message.edit_text(
        "╰_╯ <b>BROADCAST STARTED</b>\n\n"
        "Ads are being sent to all your groups/channels.\n"
        "Use Stop Ads ⏸️ to stop broadcasting.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data="dashboard"
                )
            ]
        ])
    )