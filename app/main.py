from fastapi import FastAPI, Request
from webexteamssdk import WebexTeamsAPI
from dotenv import load_dotenv
import os
import subprocess

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

    print("Webhook Received:")
    print(data)

    try:
        message_id = data["data"]["id"]
        message = webex_api.messages.get(message_id)

        if message.personEmail.endswith("@webex.bot"):
            return {"status": "ignored bot message"}

        incoming_text = message.text.strip()
        command = incoming_text.lower()

        print(f"Message Received: {incoming_text}")

        if command in ["help", "/help"]:
            reply = """
Drummond NetOps Bot Commands

/help - Show available commands
/status - Check bot status
/ping - Test connectivity
/site status OOM - Check site status
"""

        elif command in ["status", "/status"]:
            reply = "✅ Drummond NetOps Bot is online and operational."

        elif command.startswith("/ping"):

            parts = incoming_text.split()

            if len(parts) < 2:
                reply = "Usage: /ping <ip or hostname>"

            else:
                target = parts[1]

                try:

                    result = subprocess.run(
                        ["ping", "-c", "4", target],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.returncode == 0:

                        reply = f"""
        ✅ Ping Successful: {target}

        {result.stdout}
        """

                    else:

                        reply = f"""
        ❌ Ping Failed: {target}

        {result.stderr}
        """

                except Exception as e:

                    reply = f"Error running ping: {str(e)}"

        elif command.startswith("/site status"):
            site_name = command.replace("/site status", "").strip().upper()

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

        webex_api.messages.create(
            roomId=message.roomId,
            text=reply
        )

        return {"status": "success"}

    except Exception as e:
        print("ERROR:")
        print(e)
        return {"status": "error"}