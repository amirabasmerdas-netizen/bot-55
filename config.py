import os
from dotenv import load_dotenv

load_dotenv()

# Core Bot Settings
BOT_TOKEN = os.getenv("BOT_TOKEN", "8994269851:AAHgu9N4zPZhHmSsDn-I3nUxr4u9_Yl59TM")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8852010090")) # Owner Telegram ID

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

# Predefined groups for forwarding views (Channel/Group IDs or @usernames)
TARGET_GROUPS = ["@testingamele55", "@target_group_2"]
