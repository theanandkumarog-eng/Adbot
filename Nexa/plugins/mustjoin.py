from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden

from Nexa.bot import bot
from Nexa.plugins.start import send_start_menu

MUST_JOIN_CHANNEL = "Adxers"
MUST_JOIN_GROUP = "AdxersChat"

MUSTJOIN_IMAGE = "https://files.catbox.moe/43767f.jpg"

WELCOME_TEXT = """
╰_╯**WELCOME TO @ADXERS FREE ADS BOT**

To unlock the full **Theodron** experience, please join our official channel and group first!

Tip: Click the buttons below to join both. After joining, click 'Try Again' to proceed.

Your Free premium automation journey starts here
"""

@bot.on_message(filters.incoming & filters.private, group=-1)
async def must_join_handler(client: Client, msg: Message):
    if not msg.from_user:
        return
    try:
        await client.get_chat_member(MUST_JOIN_CHANNEL, msg.from_user.id)
        await client.get_chat_member(MUST_JOIN_GROUP, msg.from_user.id)
    except UserNotParticipant:
        channel_link = f"https://t.me/{MUST_JOIN_CHANNEL}"
        group_link = f"https://t.me/{MUST_JOIN_GROUP}"
        try:
            await msg.reply_photo(
                photo=MUSTJOIN_IMAGE,
                caption=WELCOME_TEXT,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Join Channel", url=channel_link)],
                        [InlineKeyboardButton("Join Group", url=group_link)],
                        [InlineKeyboardButton("Try Again", callback_data="mustjoin_retry")]
                    ]
                )
            )
            await msg.stop_propagation()
        except ChatWriteForbidden:
            pass
    except ChatAdminRequired:
        print(
            f"❌ PROMOTE BOT AS ADMIN IN:\n"
            f"Channel: {MUST_JOIN_CHANNEL}\n"
            f"Group: {MUST_JOIN_GROUP}"
        )

@bot.on_callback_query(filters.regex("^mustjoin_retry$"))
async def mustjoin_retry(client: Client, query):
    try:
        await client.get_chat_member(MUST_JOIN_CHANNEL, query.from_user.id)
        await client.get_chat_member(MUST_JOIN_GROUP, query.from_user.id)
        await query.answer("✅ Access Granted!", show_alert=True)
        await query.message.delete()
        await send_start_menu(client, query.message)
    except UserNotParticipant:
        await query.answer(
            "❌ You must join both Channel and Group first!",
            show_alert=True
        )
    except ChatAdminRequired:
        print(
            f"❌ PROMOTE BOT AS ADMIN IN:\n"
            f"Channel: {MUST_JOIN_CHANNEL}\n"
            f"Group: {MUST_JOIN_GROUP}"
        )