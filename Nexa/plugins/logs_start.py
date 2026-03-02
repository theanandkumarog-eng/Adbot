from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import LOGGER_BOT_TOKEN, API_ID, API_HASH
from Nexa.database.users import get_or_create_user

logger_bot = Client(
    "logger_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=LOGGER_BOT_TOKEN
)

@logger_bot.on_message(filters.command("start") & filters.private)
async def logger_start(client, message):
    user_id = message.from_user.id

    await get_or_create_user(user_id)

    await message.reply_text(
        "✅ <b>Logger Bot Activated!</b>\n\n"
        "You will now receive advertising logs here.\n"
        "Return to the main bot and start your broadcast."
    )