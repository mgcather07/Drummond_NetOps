HELP_MENU = """
Drummond NetOps Bot Help

Categories:
/help network - Network device commands
/help cucm - CUCM / voice commands
/help admin - Admin utilities
"""

NETWORK_HELP = """
Network Commands

/ping <ip or hostname> - Ping a target
"""

CUCM_HELP = """
CUCM / Voice Commands

/cucm phone <MAC Address> - Check phone configuration and registration
/cucm free-extension <site> - Find available extension/DID
"""

ADMIN_HELP = """
Admin Commands

/status - Check bot status
"""


def get_help(command: str) -> str:
    parts = command.lower().split()

    if len(parts) == 1:
        return HELP_MENU

    category = parts[1]

    if category == "network":
        return NETWORK_HELP

    if category in ["cucm", "voice"]:
        return CUCM_HELP

    if category == "admin":
        return ADMIN_HELP

    return f"Unknown help category: {category}\n\nTry /help"