from fastapi import FastAPI, Request
from webexteamssdk import WebexTeamsAPI
import os

app = FastAPI()

WEBEX_BOT_TOKEN = "ZWFmNWU1NDctNmYwMC00Yjg0LTgyMzAtNTdkYzRmODMwZjQ5NTc2MDQyMmEtN2E5_PF84_e1b2edbc-839a-40f0-b4b4-80a2e3a7e002"

webex_api = WebexTeamsAPI(access_token=WEBEX_BOT_TOKEN)


@app.get("/")
def root():
    return {"status": "Drummond NetOps Bot Online"}


@app.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    print("Webhook Received:")
    print(data)

    try:
        message_id = data["data"]["id"]

        message = webex_api.messages.get(message_id)

        # Ignore bot's own messages
        if message.personEmail.endswith("webex.bot"):
            return {"status": "ignored"}

        incoming_text = message.text

        print(f"Message Received: {incoming_text}")

        webex_api.messages.create(
            roomId=message.roomId,
            text=f"Drummond NetOps Bot received: {incoming_text}"
        )

        return {"status": "success"}

    except Exception as e:
        print(e)
        return {"status": "error"}