import os

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Telegram API Credentials (Get from https://my.telegram.org)
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

# Telegram Bot Token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Target Channel or Group (Username or ID)
TARGET_CHAT = os.getenv("TARGET_CHAT", "@YourGroupOrChannel")

# In-Telegram Features:
# Automatically post the summary leaderboard and CSV file to the chat when a call ends
AUTO_POST_REPORT_TO_CHAT = os.getenv("AUTO_POST_REPORT_TO_CHAT", "True").lower() in ("true", "1", "yes")

# Reports directory on disk
EXPORT_CSV = True
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "reports")
