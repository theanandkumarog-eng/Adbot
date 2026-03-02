import os
from dotenv import load_dotenv

# -------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------
load_dotenv()

def require_env(name: str):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"❌ Environment variable '{name}' is missing in .env file")
    return value

# -------------------------------
# TELEGRAM API CONFIG
# -------------------------------
API_ID = int(require_env("API_ID"))
API_HASH = require_env("API_HASH")

BOT_TOKEN = require_env("BOT_TOKEN")
LOGGER_BOT_TOKEN = require_env("LOGGER_BOT_TOKEN")

MAIN_BOT_USERNAME = "AdxersAdsBot"
# -------------------------------
# DATABASE CONFIG
# -------------------------------
MONGO_URI = require_env("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "nexa_bot")

# -------------------------------
# SESSION SETTINGS
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "Nexa", "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", 5))
DEFAULT_DELAY = int(os.getenv("DEFAULT_DELAY", 300))

# -------------------------------
# UI SETTINGS
# -------------------------------
LAST_NAME = "| by @NexaCoders"
BIO_UPDATE = "Ads Powered By @NexaCoders 🚀"
HOST_SESSION = "host"

FORCE_CHANNEL = "NexaCoders"
FORCE_GROUP = "NexaCodersChat"

FORCE_JOIN_TEXT = """
**╰_╯ WELCOME TO @NEXACODERS FREE ADS BOT**

To unlock the full experience, please join our official channel and group first!

After joining, click Dashboard again 🚀
"""

START_IMAGE = os.getenv(
    "START_IMAGE",
    "https://files.catbox.moe/43767f.jpg"
)

START_TEXT = """╰_╯ Welcome to @NexaCoders **Free Ads Bot** — The Future of Telegram Automation
• Premium Ad Broadcasting  
• Smart Delays  
• Multi-Account Support  

For support contact: @NexaCoders"""

DASHBOARD_TEXT = """╰_╯ @NexaCoders **Ads DASHBOARD**
• Hosted Accounts: `{account_count}/{max_accounts}`
• Ad Message: {ad_status}
• Cycle Interval: {delay}s
• Advertising Status: {running_status}

╰_╯ Choose an action below to continue"""

# -------------------------------
# DEBUG CHECK (SAFE)
# -------------------------------
print("✅ Environment loaded successfully")
print("🤖 Main Bot Token Loaded:", BOT_TOKEN[:10], "...")
print("📊 Logger Bot Token Loaded:", LOGGER_BOT_TOKEN[:10], "...")