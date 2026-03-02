# Nexa/core/broadcast_logs.py

from telethon import TelegramClient
from config import LOGGER_BOT_TOKEN, API_ID, API_HASH
from Nexa.core.logger import logger

logger_bot = TelegramClient(
    "logger_bot_session",
    API_ID,
    API_HASH
)

_logger_started = False


async def init_logger():
    global _logger_started
    if not _logger_started:
        try:
            await logger_bot.start(bot_token=LOGGER_BOT_TOKEN)
            _logger_started = True
        except Exception as e:
            logger.error(f"Logger bot failed to start: {e}")


async def send_log(user_id: int, text: str):
    try:
        if not _logger_started:
            await init_logger()

        await logger_bot.send_message(
            entity=user_id,
            message=text,
            parse_mode="html",
            link_preview=False
        )

    except Exception as e:
        logger.error(f"Failed to send log to {user_id}: {e}")