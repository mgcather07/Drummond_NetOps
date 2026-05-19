from app.webex.help import get_help
from app.network.ping import ping_host
from app.network.show_version import show_version
from app.cucm.phones import get_phone
from app.cucm.free_extensions import get_free_extension
from app.cucm.trunks import get_sip_trunk
from app.cucm.route_plan_lookup import get_route_plan
from app.cucm.dial_plan import get_dial_plan_match
from app.cucm.call_flow import get_call_flow
from app.cucm.health import get_cucm_health
from app.config.settings import BOT_NAME, BOT_VERSION, BOT_ENVIRONMENT
from app.admin.users import handle_admin_user_command
from app.cucm.phones_eol import get_phones_eol, handle_phone_lifecycle_selection
from app.state.pending_actions import PENDING_ACTIONS


def handle_command(message_text: str, sender_email: str) -> str:

    command = message_text.strip()

    # Remove bot mention from group spaces
    if command.lower().startswith("drummond"):
        command = command[len("drummond"):].strip()

    # Normalize command
    command_lower = command.lower()

    # -----------------------------
    # PENDING INTERACTIVE ACTIONS
    # -----------------------------
    # Example:
    # User runs:
    #   /cucm phones-eol
    #
    # Bot replies with:
    #   1. Cisco 7811
    #   2. Cisco 7941
    #
    # User replies:
    #   2
    #
    # Bot shows detail report for Cisco 7941.
    # -----------------------------

    pending_response = handle_phone_lifecycle_selection(
        command=command,
        sender_email=sender_email,
        pending_actions=PENDING_ACTIONS,
    )

    if pending_response:
        return pending_response

    # -----------------------------
    # HELP COMMANDS
    # -----------------------------

    if command_lower.startswith("/help") or command_lower == "help":
        return get_help(command)

    # -----------------------------
    # ADMIN COMMANDS
    # -----------------------------

    if command_lower.startswith("/admin"):
        return handle_admin_user_command(command, sender_email)

    # -----------------------------
    # STATUS
    # -----------------------------

    if command_lower in ["status", "/status"]:
        return (
            f"✅ {BOT_NAME} is online and operational.\n\n"
            f"🧠 Version: {BOT_VERSION}\n"
            f"🌎 Environment: {BOT_ENVIRONMENT}"
        )

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

    if command_lower.startswith("/cucm phones-eol"):
        return get_phones_eol(
            command=command,
            sender_email=sender_email,
            pending_actions=PENDING_ACTIONS,
        )

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

    if command_lower in ["/cucm health", "/health cucm"]:
        return get_cucm_health(command)

    # -----------------------------
    # UNKNOWN COMMAND
    # -----------------------------

    return "❓ Unknown command. Try /help"