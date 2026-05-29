import logging

from app.admin.users import handle_admin_user_command
from app.config.settings import BOT_NAME, BOT_VERSION, BOT_ENVIRONMENT
from app.cucm.call_flow import get_call_flow
from app.cucm.dial_plan import get_dial_plan_match
from app.cucm.free_extensions import get_free_extension
from app.cucm.health import get_cucm_health
from app.cucm.phones import get_phone
from app.cucm.phones_eol import get_phones_eol, handle_phone_lifecycle_selection
from app.cucm.route_plan_lookup import get_route_plan
from app.cucm.trunks import get_sip_trunk
from app.network.ping import ping_host
from app.network.show_version import show_version
from app.security.auth import can_run_command, command_permission_denied_message
from app.state.pending_actions import PENDING_ACTIONS
from app.webex.help import get_help

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shorthand aliases — resolved before RBAC and dispatch
# Alias just rewrites the command string; permissions still apply normally.
# ---------------------------------------------------------------------------
ALIASES = {
    "/health":    "/cucm health",
    "/phone":     "/cucm phone",
    "/trunk":     "/cucm trunk",
    "/route":     "/cucm route",
    "/eol":       "/cucm phones-eol",
    "/commands":  "/help",
}


def handle_command(message_text: str, sender_email: str) -> str:

    command = message_text.strip()

    # --- Strip bot mention (group spaces) using BOT_NAME from config ---
    bot_prefix = BOT_NAME.split()[0].lower()
    if command.lower().startswith(bot_prefix):
        command = command[len(bot_prefix):].strip()

    # --- Apply shorthand aliases ---
    # Use the whole first token for the lookup so "/phone SEP..." maps correctly.
    first_token = command.split()[0].lower() if command.split() else ""
    if first_token in ALIASES:
        command = ALIASES[first_token] + command[len(first_token):]

    command_lower = command.lower()

    # -----------------------------------------------------------------------
    # PENDING INTERACTIVE ACTIONS
    # Must run BEFORE RBAC so multi-step flows aren't interrupted.
    # -----------------------------------------------------------------------
    pending_response = handle_phone_lifecycle_selection(
        command=command,
        sender_email=sender_email,
        pending_actions=PENDING_ACTIONS,
    )
    if pending_response:
        return pending_response

    # -----------------------------------------------------------------------
    # RBAC — check before dispatch
    # -----------------------------------------------------------------------
    if not can_run_command(sender_email, command):
        return command_permission_denied_message(sender_email, command)

    # -----------------------------------------------------------------------
    # HELP
    # -----------------------------------------------------------------------

    if command_lower.startswith("/help") or command_lower == "help":
        return get_help(command, sender_email)

    # -----------------------------------------------------------------------
    # ADMIN
    # -----------------------------------------------------------------------

    if command_lower.startswith("/admin"):
        return handle_admin_user_command(command, sender_email)

    # -----------------------------------------------------------------------
    # STATUS
    # -----------------------------------------------------------------------

    if command_lower in ["status", "/status"]:
        return (
            f"✅ {BOT_NAME} is online and operational.\n\n"
            f"🧠 Version: {BOT_VERSION}\n"
            f"🌎 Environment: {BOT_ENVIRONMENT}"
        )

    # -----------------------------------------------------------------------
    # NETWORK COMMANDS
    # -----------------------------------------------------------------------

    if command_lower.startswith("/ping"):
        return ping_host(command)

    if command_lower.startswith("/show version"):
        return show_version(command)

    # -----------------------------------------------------------------------
    # CUCM COMMANDS
    # Order matters: longer prefixes first so /cucm phones-eol beats /cucm phone
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # UNKNOWN COMMAND — clean catch-all
    # -----------------------------------------------------------------------
    logger.info("Unknown command from %s: %r", sender_email, command)
    return (
        f"❓ Unknown command: `{command}`\n\n"
        "Try `/help` to see available commands."
    )
