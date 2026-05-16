# app/main.py
from fastapi import FastAPI, Request
from webexteamssdk import WebexTeamsAPI
from dotenv import load_dotenv
import os

from app.webex.command_router import handle_command

app = FastAPI()

load_dotenv()

BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

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

        reply = handle_command(message.text)

        webex_api.messages.create(
            roomId=message.roomId,
            text=reply
        )

        return {"status": "success"}

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}