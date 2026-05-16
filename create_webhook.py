from webexteamssdk import WebexTeamsAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get bot token from .env
BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("WEBEX_BOT_TOKEN is missing from .env")

# Connect to Webex API
api = WebexTeamsAPI(access_token=BOT_TOKEN)

# Create webhook
webhook = api.webhooks.create(
    name="Drummond NetOps Webhook",
    targetUrl="https://8cd4-45-22-149-30.ngrok-free.app/webhook",
    resource="messages",
    event="created"
)

print("Webhook Created Successfully")
print(webhook)