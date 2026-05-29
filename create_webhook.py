"""Webex webhook upsert — create or update the Drummond NetOps webhook.

Usage:
    python create_webhook.py

Reads WEBHOOK_TARGET_URL from .env (falls back to the legacy hardcoded URL
if not set, so existing deployments don't break immediately).
"""

import os

from dotenv import load_dotenv
from webexteamssdk import WebexTeamsAPI

load_dotenv()

BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("WEBEX_BOT_TOKEN is missing from .env")

TARGET_URL = os.getenv("WEBHOOK_TARGET_URL")
if not TARGET_URL:
    raise ValueError(
        "WEBHOOK_TARGET_URL is missing from .env\n"
        "Set it to your public HTTPS URL + /webhook, e.g.:\n"
        "  WEBHOOK_TARGET_URL=https://abc123.ngrok-free.app/webhook"
    )

WEBHOOK_NAME = "Drummond NetOps Webhook"
WEBHOOK_SECRET = os.getenv("WEBEX_WEBHOOK_SECRET")  # optional but recommended

api = WebexTeamsAPI(access_token=BOT_TOKEN)

# --- Upsert: update existing webhook if found, else create ---
existing = None
for wh in api.webhooks.list():
    if wh.name == WEBHOOK_NAME:
        existing = wh
        break

kwargs = dict(
    name=WEBHOOK_NAME,
    targetUrl=TARGET_URL,
    resource="messages",
    event="created",
)
if WEBHOOK_SECRET:
    kwargs["secret"] = WEBHOOK_SECRET

if existing:
    webhook = api.webhooks.update(
        webhookId=existing.id,
        name=WEBHOOK_NAME,
        targetUrl=TARGET_URL,
    )
    print(f"✅ Webhook UPDATED: {webhook.id}")
else:
    webhook = api.webhooks.create(**kwargs)
    print(f"✅ Webhook CREATED: {webhook.id}")

print(f"   URL:    {webhook.targetUrl}")
print(f"   Status: {webhook.status}")
