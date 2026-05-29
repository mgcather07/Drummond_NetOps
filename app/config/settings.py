# app/config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "Drummond NetOps Bot")
BOT_VERSION = os.getenv("BOT_VERSION", "0.1.0")
BOT_ENVIRONMENT = os.getenv("BOT_ENVIRONMENT", "Development")


# ---------------------------------------------------------------------------
# Startup env validation
# ---------------------------------------------------------------------------

_REQUIRED_VARS = [
    "WEBEX_BOT_TOKEN",
    "CUCM_HOST",
    "CUCM_USERNAME",
    "CUCM_PASSWORD",
    "CUCM_SSH_USERNAME",
    "CUCM_SSH_PASSWORD",
    "NETWORK_USERNAME",
    "NETWORK_PASSWORD",
    "SQL_SERVER",
    "SQL_DATABASE",
    "BOT_ADMIN_ROOM_ID",
]

# SQL creds only required when using SQL auth (default)
_SQL_AUTH_VARS = ["SQL_USERNAME", "SQL_PASSWORD"]


def validate_env() -> None:
    """Raise RuntimeError listing every missing required env var."""
    missing = [v for v in _REQUIRED_VARS if not os.getenv(v)]

    sql_auth_mode = os.getenv("SQL_AUTH_MODE", "sql").lower()
    if sql_auth_mode != "windows":
        missing += [v for v in _SQL_AUTH_VARS if not os.getenv(v)]

    if missing:
        raise RuntimeError(
            "Missing required environment variables:\n  "
            + "\n  ".join(missing)
            + "\n\nSet them in .env before starting the bot."
        )
