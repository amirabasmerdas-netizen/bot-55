import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
TARGET_GROUPS = ["@testingamele55", "@target_group_2"]
