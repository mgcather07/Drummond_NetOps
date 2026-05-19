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

/cucm health
Show CUCM health summary including AXL status, route plan access, and SIP trunk registration

/cucm phones-eol - Show CUCM phone EOL summary
/cucm phones-eol detail - Show detailed EOL/EOS phone catalog

/cucm phone <MAC Address>
Check phone configuration, lines, registration status, IP address, firmware, and active CUCM node

/cucm trunk <site or alias>
Check SIP trunk configuration, destinations, and live trunk status

/cucm free-extension <site>
Find available extension/DID validated against the CUCM route plan

/cucm route-plan <pattern>
Search CUCM route plan objects including DNs, translation patterns, and route patterns

/cucm call-flow <number> from <site>
Analyze CUCM call routing flow including route patterns, partitions, outbound trunks, and digit manipulation
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