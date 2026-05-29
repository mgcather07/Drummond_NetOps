# app/data/network_devices.py
"""
Named network device registry.

Keys are canonical device names (uppercase).
Used by the device resolver so commands accept either a name or raw IP.

device_type: Netmiko device type string
  cisco_ios    — IOS / IOS-XE
  cisco_nxos   — NX-OS (Nexus)
  cisco_xr     — IOS-XR

Update this file (and restart the bot) when devices are added or IPs change.
"""

NETWORK_DEVICES: dict = {
    # -----------------------------------------------------------------
    # Core / Distribution
    # -----------------------------------------------------------------
    # "CORE-SW1": {
    #     "host": "10.10.1.10",
    #     "device_type": "cisco_ios",
    #     "group": "core",
    #     "description": "Core distribution switch",
    # },
    # "CORE-SW2": {
    #     "host": "10.10.1.11",
    #     "device_type": "cisco_ios",
    #     "group": "core",
    #     "description": "Core distribution switch (secondary)",
    # },

    # -----------------------------------------------------------------
    # WAN / Edge
    # -----------------------------------------------------------------
    # "WAN-ROUTER-1": {
    #     "host": "10.10.0.1",
    #     "device_type": "cisco_ios",
    #     "group": "wan",
    #     "description": "WAN edge router",
    # },

    # -----------------------------------------------------------------
    # Access switches — Building A
    # -----------------------------------------------------------------
    # "ACC-BLDGA-1": {
    #     "host": "10.10.2.10",
    #     "device_type": "cisco_ios",
    #     "group": "access",
    #     "description": "Building A access switch floor 1",
    # },
}
