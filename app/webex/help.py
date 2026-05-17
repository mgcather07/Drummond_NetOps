HELP_MENU = """
Drummond NetOps Bot Help

Categories:
/help network - Network device commands
/help cucm - CUCM / voice commands
/help palo - Palo Alto firewall commands
/help vsphere - VMware / vSphere commands
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
/show version <hostname> - Show Cisco device version
"""

CUCM_HELP = """
CUCM / Voice Commands

/cucm phone <SEP device name> - Check phone configuration and registration
/cucm extension <ext> - Lookup existing extension info
/cucm free-extension <site> - Find available extension/DID
/cucm user <userid> - Lookup CUCM end user info
/cucm gateway <site> - Check voice gateway status
/cucm trunk <name> - Check SIP trunk status
/cucm dbreplication - Check DB replication
/cucm services - Check CUCM services
/cucm route <dialed number> - Analyze route pattern / dial plan match
"""

PALO_HELP = """
Palo Alto Commands

/palo status <firewall> - Check firewall health
/palo ha <firewall> - Check HA status
/palo interfaces <firewall> - Show interface status
/palo vpn <firewall> - Check VPN tunnel status
/palo sessions <firewall> - Show active session summary
/palo threats <firewall> - Show recent threat summary
/palo commits <firewall> - Show recent commits
/palo system-info <firewall> - Show PAN-OS and system info
"""

VSPHERE_HELP = """
vSphere Commands

/vsphere status - Check vCenter connection and summary
/vsphere hosts - List ESXi hosts and health state
/vsphere host <hostname> - Show ESXi host details
/vsphere vms - List critical VMs and power state
/vsphere vm <vm name> - Show VM power state, host, CPU, and memory
/vsphere snapshots - List VMs with active snapshots
/vsphere datastore - Show datastore usage summary
/vsphere cluster <cluster name> - Show cluster health and capacity
/vsphere tools <vm name> - Check VMware Tools status for a VM
"""

REPORTS_HELP = """
Reports Commands

/report did <site> - Generate DID utilization summary
/report unused-dids <site> - List unused DIDs
/report phones unregistered - Show unregistered phones
/report site health <site> - Generate site health summary
/report inventory - Show known device inventory
/report changes - Show recent automation actions
/report cucm phones - Generate CUCM phone inventory report
/report network uptime - Generate network uptime summary
"""

ADMIN_HELP = """
Admin Commands

/status - Check bot status
/version - Show bot version
/about - Show bot description
/webhooks list - List active Webex webhooks
/webhooks reset - Reset Webex webhooks
/logs recent - Show recent bot logs
/config check - Validate bot configuration
/health - Run bot health check
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

    if category in ["vsphere", "vmware", "vcenter"]:
        return VSPHERE_HELP

    if category in ["reports", "reporting"]:
        return REPORTS_HELP

    if category == "admin":
        return ADMIN_HELP

    return f"Unknown help category: {category}\n\nTry /help"