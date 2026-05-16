from fastapi import FastAPI, Request
from webexteamssdk import WebexTeamsAPI

app = FastAPI()

# Your Webex Bot Token
BOT_TOKEN = "ZWFmNWU1NDctNmYwMC00Yjg0LTgyMzAtNTdkYzRmODMwZjQ5NTc2MDQyMmEtN2E5_PF84_e1b2edbc-839a-40f0-b4b4-80a2e3a7e002"

# Connect to Webex API
webex_api = WebexTeamsAPI(access_token=BOT_TOKEN)


@app.get("/")
def root():
    return {"status": "Drummond NetOps Bot Online"}


@app.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    print("Webhook Received:")
    print(data)

    try:

        # Get Webex message ID
        message_id = data["data"]["id"]

        # Pull full message details
        message = webex_api.messages.get(message_id)

        # Ignore messages from bots
        if message.personEmail.endswith("@webex.bot"):
            return {"status": "ignored bot message"}

        # Get incoming text
        incoming_text = message.text.strip().lower()

        print(f"Message Received: {incoming_text}")

        # -----------------------------
        # COMMAND HANDLING
        # -----------------------------

        if incoming_text in ["help", "/help"]:

            reply = """
Drummond NetOps Bot Commands

/help - Show available commands
/status - Check bot status
/ping - Test connectivity
/site status OOM - Check site status
"""

        elif incoming_text in ["status", "/status"]:

            reply = "✅ Drummond NetOps Bot is online and operational."

        elif incoming_text in ["ping", "/ping"]:

            reply = "🏓 Pong! Connectivity is working."

        elif incoming_text.startswith("/site status"):

            site_name = incoming_text.replace("/site status", "").strip().upper()

            if not site_name:
                reply = "Please provide a site name. Example: /site status OOM"

            else:
                reply = f"""
📡 Site Status: {site_name}

Router: Online
WAN: Reachable
Voice Gateway: Online
Switches: Healthy

⚠️ Demo data only — live checks coming soon.
"""

        else:

            reply = "❓ Unknown command. Try /help"

        # Send response back to Webex
        webex_api.messages.create(
            roomId=message.roomId,
            text=reply
        )

        return {"status": "success"}

    except Exception as e:

        print("ERROR:")
        print(e)

        return {"status": "error"}