from pyrogram import idle
from Nexa.bot import bot
from Nexa.plugins.logs_start import logger_bot

import Nexa.plugins


def main():
    print("💡 Starting Ads Bot...")
    print("🔌 Loading plugins...")

    try:
        bot.start()
        logger_bot.start()

        print("✅ Both Bots Running Successfully!")

        idle()  # Keep running

    except KeyboardInterrupt:
        print("🛑 Bot stopped manually (Ctrl+C)")

    except Exception as e:
        print(f"❌ Bot crashed: {e}")

    finally:
        print("⏹ Shutting down...")

        try:
            if bot.is_connected:
                bot.stop()
        except:
            pass

        try:
            if logger_bot.is_connected:
                logger_bot.stop()
        except:
            pass

        print("✅ Clean Shutdown Complete.")


if __name__ == "__main__":
    main()