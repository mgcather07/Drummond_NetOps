from app.webex.help import get_help
from app.network.ping import ping_host
from app.network.show_version import show_version
from app.cucm.phones import get_phone
from app.cucm.extensions import get_free_extension


def handle_command(message_text: str) -> str:

    command = message_text.strip()

    # Remove bot mention from group spaces
    if command.lower().startswith("drummond"):
        command = command[len("drummond"):].strip()

    # Normalize command
    command_lower = command.lower()

    # -----------------------------
    # HELP COMMANDS
    # -----------------------------

    if command_lower.startswith("/help") or command_lower == "help":
        return get_help(command)

    # -----------------------------
    # STATUS
    # -----------------------------

    if command_lower in ["status", "/status"]:
        return "✅ Drummond NetOps Bot is online and operational."

    # -----------------------------
    # NETWORK COMMANDS
    # -----------------------------

    if command_lower.startswith("/ping"):
        return ping_host(command)

    if command_lower.startswith("/show version"):
        return show_version(command)

    # -----------------------------
    # CUCM COMMANDS
    # -----------------------------

    if command_lower.startswith("/cucm phone"):
        return get_phone(command)

    if command_lower.startswith("/cucm free-extension"):
        return get_free_extension(command)

    # -----------------------------
    # UNKNOWN COMMAND
    # -----------------------------

    return "❓ Unknown command. Try /help"