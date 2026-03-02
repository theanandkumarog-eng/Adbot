from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
from Nexa.bot import bot
from Nexa.database.users import users_db
import os

def generate_progress_bar(percent: int) -> str:
    percent = max(0, min(percent, 100))
    filled_blocks = percent // 10
    return "░" * filled_blocks + "▓" * (10 - filled_blocks)

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

@bot.on_callback_query(filters.regex("^analytics$"))
async def analytics_menu_callback(client, query):
    await query.answer()
    user_id = query.from_user.id
    user = await users_db.find_one({"_id": user_id})

    if not user:
        await query.answer("No analytics data found.", show_alert=True)
        return

    broadcasts = int(user.get("broadcast_completed", 0))
    sent = int(user.get("messages_sent", 0))
    failed = int(user.get("messages_failed", 0))
    logger_fail = int(user.get("logger_failures", 0))
    accounts = user.get("accounts", [])
    delay = int(user.get("delay", 300))

    status_map = user.get("account_status", {})
    total_accounts = len(accounts)
    active_accounts = 0
    inactive_accounts = 0

    for acc in accounts:
        session_name_clean = acc.replace("+", "").strip()
        status = status_map.get(session_name_clean)
        if status == "active":
            active_accounts += 1
        elif status == "inactive":
            inactive_accounts += 1
        else:
            inactive_accounts += 1

    total_messages = sent + failed
    success_rate = int((sent / total_messages) * 100) if total_messages > 0 else 0
    progress_bar = generate_progress_bar(success_rate)

    text = (
        "<b>╰_╯ Nexa Analytics</b>\n\n"
        f"<u>Broadcast Cycles Completed:</u> <b>{broadcasts}</b>\n"
        f"<b>Total Messages Sent:</b> {sent}\n"
        f"<b>Total Failed Sends:</b> {failed}\n"
        f"<b>Logger Failures:</b> {logger_fail}\n"
        f"<b>Total Accounts:</b> {total_accounts}\n"
        f"<u>Active:</u> {active_accounts} | <u>Inactive:</u> {inactive_accounts}\n"
        f"<u>Delay:</u> <code>{delay}s</code>\n\n"
        f"<b>Success Rate:</b>\n{progress_bar} {success_rate}%"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Detailed Report", callback_data="detailed_report")],
            [InlineKeyboardButton("Back", callback_data="dashboard")]
        ]
    )

    await safe_edit(query, text, keyboard)