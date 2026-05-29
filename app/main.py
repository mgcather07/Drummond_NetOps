# app/main.py
import asyncio
import hashlib
import hmac
import json
import logging
import os
from functools import partial

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from webexteamssdk import WebexTeamsAPI

# ---------------------------------------------------------------------------
# Logging — configure once at import time before any module logger is used
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("netops")

from app.config.settings import validate_env
from app.security.auth import is_authorized, unauthorized_message
from app.webex.command_router import handle_command

load_dotenv()

app = FastAPI()


@app.on_event("startup")
def on_startup():
    validate_env()


BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")
ADMIN_ROOM_ID = os.getenv("BOT_ADMIN_ROOM_ID")
WEBHOOK_SECRET = os.getenv("WEBEX_WEBHOOK_SECRET")

if not BOT_TOKEN:
    raise ValueError("WEBEX_BOT_TOKEN is missing from .env")

webex_api = WebexTeamsAPI(access_token=BOT_TOKEN)


def _verify_signature(raw_body: bytes, header_sig: str) -> bool:
    """Return True if the X-Spark-Signature header matches the HMAC-SHA1 of the body."""
    if not WEBHOOK_SECRET:
        # Secret not configured — skip validation (allows gradual rollout)
        return True
    expected = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha1,
    ).hexdigest()
    return hmac.compare_digest(expected, header_sig or "")


@app.get("/")
def root():
    return {"status": "Drummond NetOps Bot Online"}


@app.post("/webhook")
async def webhook(request: Request):
    raw_body = await request.body()

    # --- Signature validation ---
    sig = request.headers.get("X-Spark-Signature", "")
    if not _verify_signature(raw_body, sig):
        return Response(content="Invalid signature", status_code=403)

    try:
        data = json.loads(raw_body)
        message_id = data["data"]["id"]
        loop = asyncio.get_running_loop()
        message = await loop.run_in_executor(None, webex_api.messages.get, message_id)

        if message.personEmail.endswith("@webex.bot"):
            return {"status": "ignored bot message"}

        sender_email = message.personEmail.lower()

        if not is_authorized(sender_email):
            denied_message = unauthorized_message(sender_email)

            webex_api.messages.create(
                roomId=message.roomId,
                text=denied_message
            )

            if ADMIN_ROOM_ID:
                webex_api.messages.create(
                    roomId=ADMIN_ROOM_ID,
                    text=(
                        f"🚨 Unauthorized Bot Access Attempt\n\n"
                        f"Email: {sender_email}\n"
                        f"Command: {message.text}\n"
                        f"Room Type: {message.roomType}\n"
                        f"Action: Blocked"
                    )
                )

            return {"status": "unauthorized"}

        incoming_text = message.text.strip().lower()

        if incoming_text in ["/cucm health", "/health cucm", "/health"]:
            webex_api.messages.create(
                roomId=message.roomId,
                text="⏳ CUCM health check started. DB replication can take 30–60 seconds..."
            )

        # Run blocking handler in thread pool so the async loop stays free
        reply = await loop.run_in_executor(
            None,
            partial(handle_command, message_text=message.text, sender_email=sender_email)
        )

        await loop.run_in_executor(
            None,
            partial(webex_api.messages.create, roomId=message.roomId, text=reply)
        )

        return {"status": "success"}

    except Exception as e:
        logger.exception("Webhook handler error: %s", e)
        return {"status": "error"}
