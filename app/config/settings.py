# app/config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "Drummond NetOps Bot")
BOT_VERSION = os.getenv("BOT_VERSION", "0.1.0")
BOT_ENVIRONMENT = os.getenv("BOT_ENVIRONMENT", "Development")


