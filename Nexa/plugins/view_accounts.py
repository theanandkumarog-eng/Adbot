import os
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
from telethon import TelegramClient
from telethon.errors import AuthKeyUnregisteredError

from Nexa.bot import bot
from config import API_ID, API_HASH, SESSION_DIR
from Nexa.database.users import users_db

os.makedirs(SESSION_DIR, exist_ok=True)

def clean_phone(phone: str):
    phone = str(phone).replace("+", "").strip()
    return f"+{phone}"

def get_session_path(user_id: int, session_name: str):
    session_name_clean = session_name.replace("+", "").strip()
    return os.path.join(SESSION_DIR, f"{user_id}_{session_name_clean}.session")

async def check_status(user_id: int, session_name: str):
    user = await users_db.find_one({"_id": user_id})
    status_map = user.get("account_status", {}) if user else {}
    
    session_name_clean = session_name.replace("+", "").strip()
    
    if status_map.get(session_name_clean) == "inactive":
        return "Inactive", "❌"
    
    session_path = get_session_path(user_id, session_name)
    
    if not os.path.isfile(session_path):
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {f"account_status.{session_name_clean}": "inactive"}}
        )
        return "Inactive", "❌"
    
    client = None
    try:
        base_path = session_path.replace(".session", "")
        client = TelegramClient(base_path, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await users_db.update_one(
                {"_id": user_id},
                {"$set": {f"account_status.{session_name_clean}": "inactive"}}
            )
            return "Inactive", "❌"
        
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {f"account_status.{session_name_clean}": "active"}}
        )
        return "Active", "✅"
    
    except AuthKeyUnregisteredError:
        await users_db.update_one(
            {"_id": user_id},
            {"$set": {f"account_status.{session_name_clean}": "inactive"}}
        )
        return "Inactive", "❌"
    
    except Exception:
        return "Inactive", "❌"
    
    finally:
        if client:
            try:
                await client.disconnect()
            except:
                pass

@bot.on_callback_query(filters.regex("^view_accounts$"))
async def view_accounts(client, query):
    await query.answer()
    user_id = query.from_user.id

    user = await users_db.find_one({"_id": user_id})
    accounts = user.get("accounts", []) if user else []

    if not accounts:
        text = "╰_╯ NO ACCOUNTS TO DELETE\n\nAdd an account to start Advertising!"
        buttons = [[
            InlineKeyboardButton("Add Account", callback_data="host_account"),
            InlineKeyboardButton("Back", callback_data="dashboard")
        ]]
        return await safe_edit(query, text, buttons)

    text = "╰_╯ HOSTED ACCOUNTS\n\n"
    buttons = []

    status_tasks = [check_status(user_id, acc) for acc in accounts]
    statuses = await asyncio.gather(*status_tasks, return_exceptions=True)
    
    for idx, (session_name, status_info) in enumerate(zip(accounts, statuses), start=1):
        if isinstance(status_info, Exception):
            status, emoji = "Inactive", "❌"
        else:
            status, emoji = status_info
        
        phone = clean_phone(session_name)
        text += f"{idx}. {phone} - {status} {emoji}\n"
        
        buttons.append([
            InlineKeyboardButton(
                f"{phone} ({status} {emoji})",
                callback_data="ignore"
            ),
            InlineKeyboardButton(
                "Delete",
                callback_data=f"confirmdelete_{session_name}"
            )
        ])

    text += "\n╰_╯ Choose an action:"
    buttons.append([InlineKeyboardButton("Add Account", callback_data="host_account")])
    buttons.append([InlineKeyboardButton("Back", callback_data="dashboard")])

    await safe_edit(query, text, buttons)

async def safe_edit(query, text, buttons):
    try:
        keyboard = InlineKeyboardMarkup(buttons)
        if hasattr(query.message, 'photo') and query.message.photo:
            await query.message.edit_caption(
                caption=text,
                reply_markup=keyboard
            )
        else:
            await query.message.edit_text(
                text=text,
                reply_markup=keyboard
            )
    except RPCError:
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except:
            pass