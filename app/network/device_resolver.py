# app/network/device_resolver.py
"""
Resolve a device name or raw IP to a Netmiko connection dict.

Accepts:
  "CORE-SW1"     — looks up in NETWORK_DEVICES registry (case-insensitive)
  "10.10.1.10"   — treated as a raw IP with default cisco_ios device type

Raises ValueError with a user-friendly message if the name is unknown
and the input is not a valid IP address.
"""

import ipaddress
import logging
import os

from app.data.network_devices import NETWORK_DEVICES

logger = logging.getLogger(__name__)

_DEFAULT_DEVICE_TYPE = "cisco_ios"


def resolve_device(name_or_ip: str) -> dict:
    """
    Return a Netmiko-compatible device dict:
      {"name": str, "host": str, "device_type": str,
       "username": str, "password": str,
       "disabled_algorithms": {...}}

    Raises ValueError if the input is neither a registered device name
    nor a valid IP address.
    """
    key = name_or_ip.upper()

    if key in NETWORK_DEVICES:
        entry = NETWORK_DEVICES[key].copy()
        device = {
            "name": key,
            "host": entry["host"],
            "device_type": entry.get("device_type", _DEFAULT_DEVICE_TYPE),
            "username": os.getenv("NETWORK_USERNAME"),
            "password": os.getenv("NETWORK_PASSWORD"),
            "disabled_algorithms": {
                "kex": [
                    "diffie-hellman-group16-sha512",
                    "diffie-hellman-group18-sha512",
                    "diffie-hellman-group14-sha256",
                    "diffie-hellman-group-exchange-sha256",
                ]
            },
        }
        logger.debug("Resolved device %s → %s", key, entry["host"])
        return device

    # Try raw IP fallback
    try:
        ipaddress.ip_address(name_or_ip)
        logger.debug("Using raw IP: %s", name_or_ip)
        return {
            "name": name_or_ip,
            "host": name_or_ip,
            "device_type": _DEFAULT_DEVICE_TYPE,
            "username": os.getenv("NETWORK_USERNAME"),
            "password": os.getenv("NETWORK_PASSWORD"),
            "disabled_algorithms": {
                "kex": [
                    "diffie-hellman-group16-sha512",
                    "diffie-hellman-group18-sha512",
                    "diffie-hellman-group14-sha256",
                    "diffie-hellman-group-exchange-sha256",
                ]
            },
        }
    except ValueError:
        pass

    registered = sorted(NETWORK_DEVICES.keys())
    hint = (
        f"Unknown device: `{name_or_ip}`.\n"
        "Use `/net devices` to list registered devices, or pass a raw IP address."
    )
    if not registered:
        hint += "\n\n(No devices are registered yet — add them to `app/data/network_devices.py`.)"
    raise ValueError(hint)
