# app/network/arp_mac.py
"""
TASK-021: ARP table and MAC address table lookups.

Commands:
  /net arp <device> <ip>    — ARP entry for an IP on a device
  /net mac <device> <mac>   — MAC address table entry on a device
"""

import logging
import re

from netmiko import ConnectHandler

from app.network.device_resolver import resolve_device

logger = logging.getLogger(__name__)


def normalize_mac(mac: str) -> str:
    """
    Accept aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, or aabb.ccdd.eeff.
    Returns IOS dotted-quad notation: aabb.ccdd.eeff (lowercase).
    Raises ValueError on invalid input.
    """
    clean = re.sub(r"[:\-\.]", "", mac).lower()
    if len(clean) != 12 or not re.fullmatch(r"[0-9a-f]{12}", clean):
        raise ValueError(f"Invalid MAC address: `{mac}`\n\nExpected formats: aa:bb:cc:dd:ee:ff  or  aabb.ccdd.eeff")
    return f"{clean[0:4]}.{clean[4:8]}.{clean[8:12]}"


def arp_lookup(device_name: str, ip: str) -> str:
    try:
        device = resolve_device(device_name)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = conn.send_command(f"show ip arp {ip}")
        conn.disconnect()

        if not output or "Protocol" not in output:
            return f"🔍 ARP Lookup: {ip} on {device_name}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\nNo ARP entry found for {ip}."

        lines_out = ["🔍 ARP Lookup", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for line in output.splitlines():
            if ip in line:
                parts = line.split()
                if len(parts) >= 6:
                    lines_out.append(f"IP:        {parts[1]}")
                    lines_out.append(f"Age:       {parts[2]} min")
                    lines_out.append(f"MAC:       {parts[3]}")
                    lines_out.append(f"Interface: {parts[5]}")
                else:
                    lines_out.append(line)
                break

        return "\n".join(lines_out)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("ARP lookup failed on %s for %s", device_name, ip)
        return error(translate_exception(e), hint=f"Check that {device_name} ({host}) is reachable.")


def mac_lookup(device_name: str, mac_input: str) -> str:
    try:
        mac = normalize_mac(mac_input)
    except ValueError as e:
        return str(e)

    try:
        device = resolve_device(device_name)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = conn.send_command(f"show mac address-table address {mac}", read_timeout=30)
        conn.disconnect()

        if not output or mac not in output.lower():
            return (
                f"🔍 MAC Lookup: {mac} on {device_name}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"MAC {mac} not found on {device_name}."
            )

        lines_out = [f"🔍 MAC Lookup: {mac} on {device_name}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for line in output.splitlines():
            if mac.replace(".", "").lower() in line.replace(".", "").replace(":", "").replace("-", "").lower():
                parts = line.split()
                if len(parts) >= 4:
                    lines_out.append(f"VLAN:  {parts[0]}")
                    lines_out.append(f"MAC:   {parts[1]}")
                    lines_out.append(f"Type:  {parts[2]}")
                    lines_out.append(f"Port:  {parts[3]}")
                else:
                    lines_out.append(line)
                break

        return "\n".join(lines_out)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("MAC lookup failed on %s for %s", device_name, mac)
        return error(translate_exception(e), hint=f"Check that {device_name} ({host}) is reachable.")
