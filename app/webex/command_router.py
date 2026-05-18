from app.webex.help import get_help
from app.network.ping import ping_host
from app.network.show_version import show_version
from app.cucm.phones import get_phone
from app.cucm.free_extensions import get_free_extension
from app.cucm.trunks import get_sip_trunk
from app.cucm.route_plan_lookup import get_route_plan
from app.cucm.dial_plan import get_dial_plan_match
from app.cucm.call_flow import get_call_flow


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

    if command_lower.startswith("/cucm trunk"):
        return get_sip_trunk(command)

    if command_lower.startswith("/cucm call-flow"):
        return get_call_flow(command)

    if command_lower.startswith("/cucm route-plan"):
        return get_route_plan(command)

    if command_lower.startswith("/cucm route"):
        return get_dial_plan_match(command)

    # -----------------------------
    # UNKNOWN COMMAND
    # -----------------------------

    return "❓ Unknown command. Try /help"