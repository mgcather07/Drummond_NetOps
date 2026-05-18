# app/main.py
from fastapi import FastAPI, Request
from webexteamssdk import WebexTeamsAPI
from dotenv import load_dotenv
import os

from app.webex.command_router import handle_command
from app.security.auth import is_authorized, unauthorized_message

app = FastAPI()

load_dotenv()

BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")
ADMIN_ROOM_ID = os.getenv("BOT_ADMIN_ROOM_ID")

if not BOT_TOKEN:
    raise ValueError("WEBEX_BOT_TOKEN is missing from .env")

webex_api = WebexTeamsAPI(access_token=BOT_TOKEN)


@app.get("/")
def root():
    return {"status": "Drummond NetOps Bot Online"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    try:
        message_id = data["data"]["id"]
        message = webex_api.messages.get(message_id)

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
                    text=f"""🚨 Unauthorized Bot Access Attempt

            Email: {sender_email}
            Command: {message.text}
            Room Type: {message.roomType}
            Action: Blocked
            """
                )

            return {"status": "unauthorized"}

        incoming_text = message.text.strip().lower()

        if incoming_text in ["/cucm health", "/health cucm"]:
            webex_api.messages.create(
                roomId=message.roomId,
                text="⏳ CUCM health check started. DB replication can take 30–60 seconds..."
            )

        reply = handle_command(
            message_text=message.text,
            sender_email=sender_email
        )

        webex_api.messages.create(
            roomId=message.roomId,
            text=reply
        )

        return {"status": "success"}

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}