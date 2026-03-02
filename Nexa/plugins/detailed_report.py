from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
from Nexa.bot import bot
from Nexa.database.users import users_db
from datetime import datetime
import asyncio

async def safe_edit(query, text, keyboard):
    try:
        await query.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except RPCError:
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except:
            pass

@bot.on_callback_query(filters.regex("^detailed_report$"))
async def detailed_report_callback(client, query):
    await query.answer()
    user_id = query.from_user.id
    user = await users_db.find_one({"_id": user_id})

    if not user:
        await query.answer("No detailed report available.", show_alert=True)
        return

    sent = int(user.get("messages_sent", 0))
    failed = int(user.get("messages_failed", 0))
    broadcasts = int(user.get("broadcast_completed", 0))
    logger_fail = int(user.get("logger_failures", 0))
    accounts = user.get("accounts", [])
    delay = int(user.get("delay", 300))

    status_map = user.get("account_status", {})
    total_accounts = len(accounts)
    active_accounts = 0
    inactive_accounts = 0

    status_tasks = []
    for acc in accounts:
        session_name_clean = acc.replace("+", "").strip()
        status = status_map.get(session_name_clean)
        if status == "inactive":
            inactive_accounts += 1
        elif status == "active":
            active_accounts += 1
        else:
            status_tasks.append(check_live_status(user_id, acc))

    if status_tasks:
        live_results = await asyncio.gather(*status_tasks, return_exceptions=True)
        for result in live_results:
            if isinstance(result, tuple) and result[0] == "Active":
                active_accounts += 1
            elif isinstance(result, tuple):
                inactive_accounts += 1

    today = datetime.now().strftime("%d/%m/%y")

    text = (
        "<b>╰_╯ DETAILED ANALYTICS REPORT:</b>\n\n"
        f"<u>Date:</u> {today}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        "<b>Broadcast Stats:</b>\n"
        f"- <u>Total Sent:</u> {sent}\n"
        f"- <u>Total Failed:</u> {failed}\n"
        f"- <u>Total Broadcasts:</u> {broadcasts}\n\n"
        "<b>Logger Stats:</b>\n"
        f"- <u>Logger Failures:</u> {logger_fail}\n\n"
        "<b>Account Stats:</b>\n"
        f"- Total Accounts: <u>{total_accounts}</u>\n"
        f"- <b>Active Accounts:</b> {active_accounts} 🟢\n"
        f"- <u>Inactive Accounts:</u> {inactive_accounts} 🔴\n\n"
        f"<b>Current Delay:</b> <code>{delay}s</code>"
    )

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Back", callback_data="analytics")]]
    )

    await safe_edit(query, text, keyboard)

async def check_live_status(user_id: int, session_name: str):
    from config import API_ID, API_HASH, SESSION_DIR
    from telethon import TelegramClient
    from telethon.errors import AuthKeyUnregisteredError
    
    session_path = f"{SESSION_DIR}/{user_id}_{session_name.replace('+', '').strip()}.session"
    session_base = session_path.replace(".session", "")
    
    if not os.path.exists(session_path):
        return "Inactive", "❌"
    
    client = None
    try:
        client = TelegramClient(session_base, API_ID, API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            return "Active", "✅"
        return "Inactive", "❌"
    except AuthKeyUnregisteredError:
        return "Inactive", "❌"
    except:
        return "Inactive", "❌"
    finally:
        if client:
            try:
                await client.disconnect()
            except:
                pass