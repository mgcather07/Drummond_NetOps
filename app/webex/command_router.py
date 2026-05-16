from app.webex.help import get_help
from app.network.ping import ping_host


def handle_command(message_text: str) -> str:
    command = message_text.strip()

    if command.lower().startswith("/help") or command.lower() == "help":
        return get_help(command)

    if command.lower() in ["status", "/status"]:
        return "✅ Drummond NetOps Bot is online and operational."

    if command.lower().startswith("/ping"):
        return ping_host(command)

    return "❓ Unknown command. Try /help"