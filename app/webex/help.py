HELP_MENU = """
Drummond NetOps Bot Help

Categories:
/help network - Network device commands
/help cucm - CUCM / voice commands
/help palo - Palo Alto firewall commands
/help reports - Reporting commands
/help admin - Admin utilities
"""

NETWORK_HELP = """
Network Commands

/ping <ip or hostname> - Ping a target
/traceroute <ip or hostname> - Trace route to a target
/site status <site> - Check site health
/switch health <hostname> - Check switch health
/interface errors <hostname> - Check interface errors
/device uptime <hostname> - Show device uptime
"""

CUCM_HELP = """
CUCM / Voice Commands

/check phone <SEP MAC> - Check phone registration
/check extension <ext> - Lookup extension info
/cucm dbreplication - Check DB replication
/cucm services - Check CUCM services
/gateway status <site> - Check voice gateway status
"""

PALO_HELP = """
Palo Alto Commands

/palo status <firewall> - Check firewall health
/palo ha <firewall> - Check HA status
/palo interfaces <firewall> - Show interface status
/palo vpn <firewall> - Check VPN tunnel status
/palo sessions <firewall> - Show active session summary
/palo threats <firewall> - Show recent threat summary
"""

REPORTS_HELP = """
Reports Commands

/report did <site> - Generate DID utilization summary
/report unused-dids <site> - List unused DIDs
/report phones unregistered - Show unregistered phones
/report site health <site> - Generate site health summary
/report inventory - Show known device inventory
/report changes - Show recent automation actions
"""

ADMIN_HELP = """
Admin Commands

/status - Check bot status
/version - Show bot version
/about - Show bot description
/webhooks list - List active Webex webhooks
/webhooks reset - Reset Webex webhooks
/logs recent - Show recent bot logs
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

    if category in ["palo", "firewall", "firewalls"]:
        return PALO_HELP

    if category in ["reports", "reporting"]:
        return REPORTS_HELP

    if category == "admin":
        return ADMIN_HELP

    return f"Unknown help category: {category}\n\nTry /help"