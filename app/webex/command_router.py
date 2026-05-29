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

    if command_lower.startswith("/traceroute"):
        from app.network.traceroute import traceroute_host
        return traceroute_host(command)

    # /show ip route <device> <ip> must come before /show version
    if command_lower.startswith("/show ip route"):
        from app.network.show_route import show_ip_route
        return show_ip_route(command)

    if command_lower.startswith("/show interface"):
        from app.network.show_interface import show_interface
        return show_interface(command)

    if command_lower.startswith("/show version"):
        return show_version(command)

    # -----------------------------------------------------------------------
    # NET COMMANDS (device registry, ARP/MAC, neighbors, VLAN, stats)
    # -----------------------------------------------------------------------

    if command_lower.startswith("/net"):
        parts = command.split()
        sub = parts[1].lower() if len(parts) > 1 else ""

        if sub == "devices":
            from app.data.network_devices import NETWORK_DEVICES
            if not NETWORK_DEVICES:
                return (
                    "📡 **Registered Network Devices**\n\n"
                    "No devices registered yet.\n"
                    "Add devices to `app/data/network_devices.py`."
                )
            lines = ["📡 **Registered Network Devices**\n"]
            by_group: dict = {}
            for name, info in NETWORK_DEVICES.items():
                by_group.setdefault(info.get("group", "other"), []).append((name, info))
            for group in sorted(by_group):
                lines.append(f"**{group.upper()}**")
                for name, info in sorted(by_group[group]):
                    lines.append(f"  `{name}` — {info['host']} ({info.get('description', '')})")
            return "\n".join(lines)

        if sub == "arp":
            if len(parts) < 4:
                return "Usage: `/net arp <device> <ip>`"
            from app.network.arp_mac import arp_lookup
            return arp_lookup(parts[2], parts[3])

        if sub == "mac":
            if len(parts) < 4:
                return "Usage: `/net mac <device> <mac>`"
            from app.network.arp_mac import mac_lookup
            return mac_lookup(parts[2], parts[3])

        if sub == "neighbors":
            if len(parts) < 3:
                return "Usage: `/net neighbors <device> [interface]`"
            iface = parts[3] if len(parts) > 3 else None
            from app.network.neighbors import get_neighbors
            return get_neighbors(parts[2], iface)

        if sub == "vlan":
            if len(parts) < 3:
                return "Usage: `/net vlan <device> [vlan-id]`"
            vlan_id = parts[3] if len(parts) > 3 else None
            from app.network.vlan import get_vlans
            return get_vlans(parts[2], vlan_id)

        if sub == "port":
            if len(parts) < 4:
                return "Usage: `/net port <device> <interface>`"
            from app.network.vlan import get_port_vlan
            return get_port_vlan(parts[2], parts[3])

        if sub == "stats":
            if len(parts) < 4:
                return "Usage: `/net stats <device> <interface>`"
            from app.network.stats import get_interface_stats
            return get_interface_stats(parts[2], parts[3])

        return f"❓ Unknown net subcommand: `{sub}`\n\nTry `/help network` for available commands."

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
    # PALO ALTO COMMANDS
    # -----------------------------------------------------------------------

    if command_lower.startswith("/palo"):
        parts = command.split()
        sub = parts[1].lower() if len(parts) > 1 else ""

        if sub == "policy":
            if len(parts) < 5:
                return "Usage: `/palo policy <src> <dst> <port>`"
            from app.palo.policy import get_policy_match
            return get_policy_match(parts[2], parts[3], parts[4])

        if sub == "nat":
            if len(parts) < 3:
                return "Usage: `/palo nat <ip>`"
            from app.palo.policy import get_nat_match
            return get_nat_match(parts[2])

        if sub == "health":
            from app.palo.health import get_system_health
            return get_system_health()

        if sub == "ha":
            from app.palo.health import get_ha_state
            return get_ha_state()

        if sub == "interfaces":
            from app.palo.interfaces import get_interfaces
            return get_interfaces()

        if sub == "zones":
            from app.palo.interfaces import get_zones
            return get_zones()

        if sub == "route":
            if len(parts) < 3:
                return "Usage: `/palo route <ip>`"
            from app.palo.interfaces import get_route
            return get_route(parts[2])

        if sub == "search":
            if len(parts) < 3:
                return "Usage: `/palo search <ip>`"
            from app.palo.search import search_rules_by_ip
            return search_rules_by_ip(parts[2])

        if sub == "address":
            if len(parts) < 3:
                return "Usage: `/palo address <object-name>`"
            from app.palo.search import get_address_object
            return get_address_object(" ".join(parts[2:]))

        return f"❓ Unknown palo subcommand: `{sub}`\n\nTry `/help palo` for available commands."

    # -----------------------------------------------------------------------
    # UNKNOWN COMMAND — clean catch-all
    # -----------------------------------------------------------------------
    logger.info("Unknown command from %s: %r", sender_email, command)
    return (
        f"❓ Unknown command: `{command}`\n\n"
        "Try `/help` to see available commands."
    )
