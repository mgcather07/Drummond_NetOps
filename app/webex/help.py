# app/webex/help.py
"""
Role-aware, data-driven help system.

Each command entry:  (syntax, required_permission, description)

get_help(command, sender_email) filters to only the commands the
caller's role can actually run, then formats by category.
"""

from typing import Optional
from app.security.auth import has_permission

# ---------------------------------------------------------------------------
# Command registry
# Format: (syntax, required_permission, description)
# None permission = public (always shown)
# ---------------------------------------------------------------------------

COMMANDS = {
    "general": [
        ("/help [category]",        None,               "Show this help menu"),
        ("/help cucm",              None,               "CUCM command list"),
        ("/help network",           None,               "Network command list"),
        ("/help palo",              None,               "Palo Alto command list"),
        ("/help vsphere",           None,               "vSphere command list"),
        ("/help admin",             None,               "Admin command list"),
        ("/status",                 None,               "Bot status and version"),
        ("/commands",               None,               "Alias for /help"),
    ],
    "cucm": [
        ("/cucm health",            "cucm.health",      "CUCM health: AXL, DB replication, trunks"),
        ("/cucm phone <MAC>",       "cucm.read",        "Phone config + live registration status"),
        ("/cucm trunk <alias>",     "cucm.read",        "SIP trunk config + live status"),
        ("/cucm route <number>",    "cucm.read",        "Dial plan match for a dialed number"),
        ("/cucm route-plan <pat>",  "cucm.read",        "Search CUCM route plan objects"),
        ("/cucm call-flow <num> from <site>",
                                    "cucm.read",        "Analyze call routing flow end-to-end"),
        ("/cucm free-extension <site>",
                                    "cucm.read",        "Find next available extension at a site"),
        ("/cucm phones-eol",        "cucm.read",        "EOL phone inventory by model"),
    ],
    "network": [
        ("/ping <target>",                    "network.read", "ICMP ping to an IP or hostname"),
        ("/traceroute <target>",              "network.read", "Traceroute to an IP or hostname"),
        ("/show version <device>",            "network.read", "SSH show version on a device"),
        ("/show interface <device> <iface>",  "network.read", "SSH show interfaces detail"),
        ("/show ip route <device> <ip>",      "network.read", "SSH show ip route lookup"),
        ("/net devices",                      "network.read", "List registered network devices"),
        ("/net arp <device> <ip>",            "network.read", "ARP table entry for an IP"),
        ("/net mac <device> <mac>",           "network.read", "MAC address table lookup"),
        ("/net neighbors <device> [iface]",   "network.read", "CDP/LLDP neighbor discovery"),
        ("/net vlan <device> [vlan-id]",      "network.read", "VLAN list or port members"),
        ("/net port <device> <iface>",        "network.read", "VLAN membership for a port"),
        ("/net stats <device> <iface>",       "network.read", "Interface error and rate stats"),
    ],
    "palo": [
        ("/palo policy <src> <dst> <port>",
                                    "palo.read",        "Test security policy match"),
        ("/palo nat <ip>",          "palo.read",        "Test NAT policy match"),
        ("/palo health",            "palo.read",        "System resource summary"),
        ("/palo ha",                "palo.read",        "HA pair state and sync status"),
        ("/palo interfaces",        "palo.read",        "Interface list with IP, state, zone"),
        ("/palo zones",             "palo.read",        "Security zone and member list"),
        ("/palo route <ip>",        "palo.read",        "FIB route lookup"),
        ("/palo search <ip>",       "palo.read",        "Security rules referencing an IP"),
        ("/palo address <name>",    "palo.read",        "Look up a named address object"),
    ],
    "vsphere": [
        ("/vsphere vm <name>",      "vsphere.read",     "VM power state, resources, host, IP"),
        ("/vsphere list",           "vsphere.read",     "All VMs with power state"),
        ("/vsphere hosts",          "vsphere.read",     "ESXi host health and utilization"),
        ("/vsphere cluster",        "vsphere.read",     "Cluster HA/DRS state and resources"),
        ("/vsphere datastores",     "vsphere.read",     "Datastore capacity and free space"),
        ("/vsphere net <vm>",       "vsphere.read",     "VM vNIC, port group, VLAN, guest IPs"),
        ("/vsphere portgroup <pg>", "vsphere.read",     "VMs connected to a port group"),
        ("/vsphere snapshots [vm]", "vsphere.read",     "Snapshot inventory with age flags"),
        ("/vsphere power <vm> <action>",
                                    "vsphere.write",    "Power on/off/restart VM (master only)"),
    ],
    "admin": [
        ("/admin users",            "admin.users.master", "List all authorized users by role"),
        ("/admin add-user <email> <role> <name>",
                                    "admin.users.master", "Add a new authorized user"),
        ("/admin disable-user <email>",
                                    "admin.users.master", "Disable a user (keeps their record)"),
        ("/admin enable-user <email>",
                                    "admin.users.master", "Re-enable a disabled user"),
        ("/admin set-role <email> <role>",
                                    "admin.users.master", "Change a user's role"),
    ],
}

CATEGORY_LABELS = {
    "general": "General",
    "cucm":    "CUCM / Voice",
    "network": "Network Devices",
    "palo":    "Palo Alto Firewall",
    "vsphere": "vSphere",
    "admin":   "Administration",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _can_see(email: Optional[str], permission: Optional[str]) -> bool:
    """Return True if the caller can see a command with the given permission."""
    if permission is None:
        return True
    if not email:
        return False
    return has_permission(email, permission)


def _format_category(label: str, entries: list) -> str:
    lines = [f"**{label}**"]
    for syntax, _, desc in entries:
        lines.append(f"  `{syntax}` — {desc}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_help(command: str, sender_email: Optional[str] = None) -> str:
    """
    Return role-filtered help text.

    command:       the full command string ("/help", "/help cucm", …)
    sender_email:  caller's email for permission filtering; None = public only
    """
    parts = command.strip().lower().split()
    category_arg = parts[1] if len(parts) > 1 else None

    # --- Category-specific help ---
    if category_arg and category_arg in COMMANDS:
        entries = [
            e for e in COMMANDS[category_arg]
            if _can_see(sender_email, e[1])
        ]
        if not entries:
            return f"No {CATEGORY_LABELS.get(category_arg, category_arg)} commands available for your role."
        return _format_category(CATEGORY_LABELS[category_arg], entries)

    # --- Top-level help: show categories that have at least one visible command ---
    lines = ["**Drummond NetOps Bot — Command Help**\n"]

    for cat, label in CATEGORY_LABELS.items():
        visible = [e for e in COMMANDS[cat] if _can_see(sender_email, e[1])]
        if not visible:
            continue
        count = len(visible)
        lines.append(f"  `/help {cat}` — {label} ({count} command{'s' if count != 1 else ''})")

    lines.append("\nType `/help <category>` to list commands in that category.")
    return "\n".join(lines)
