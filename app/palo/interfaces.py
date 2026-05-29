# app/palo/interfaces.py
"""
TASK-018: Palo Alto interface status, zone membership, and route lookup.

Commands:
  /palo interfaces       — interface list with IP, state, zone
  /palo zones            — security zone → member interfaces
  /palo route <ip>       — FIB route lookup
"""

import ipaddress
import logging
import xml.etree.ElementTree as ET

from app.palo.client import palo_op, palo_config_get

logger = logging.getLogger(__name__)

# Default device/vsys names for standalone PA firewalls
_DEVICE = "localhost.localdomain"
_VSYS = "vsys1"


def _text(el, path: str, default: str = "N/A") -> str:
    node = el.find(path)
    return (node.text or default).strip() if node is not None else default


def get_interfaces() -> str:
    try:
        resp = palo_op("<show><interface>all</interface></show>")
        root = ET.fromstring(resp.text)

        ifaces = root.findall(".//ifnet/entry")
        if not ifaces:
            ifaces = root.findall(".//entry")

        if not ifaces:
            return "🔥 Palo Alto Interfaces\n━━━━━━━━━━━━━━━━━━━━━━━\nNo interface data returned."

        lines = [
            "🔥 Palo Alto Interfaces",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"{'Interface':<20} {'IP':<20} {'State':<6} {'Zone'}",
            f"{'─'*20} {'─'*20} {'─'*6} {'─'*20}",
        ]
        for entry in ifaces:
            name = entry.get("name", "N/A")
            ip = _text(entry, "ip")
            state = _text(entry, "state", "N/A")
            zone = _text(entry, "zone")
            state_icon = "✅" if state.lower() == "up" else "❌"
            lines.append(f"{name:<20} {ip:<20} {state_icon:<6} {zone}")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo interfaces query failed")
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")


def get_zones() -> str:
    try:
        xpath = (
            f"/config/devices/entry[@name='{_DEVICE}']"
            f"/vsys/entry[@name='{_VSYS}']/zone"
        )
        resp = palo_config_get(xpath)
        root = ET.fromstring(resp.text)

        zones = root.findall(".//zone/entry")
        if not zones:
            zones = root.findall(".//entry")

        if not zones:
            return "🔥 Palo Alto Zones\n━━━━━━━━━━━━━━━━━━━━━\nNo zone data returned."

        lines = ["🔥 Palo Alto Security Zones", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for zone in zones:
            name = zone.get("name", "N/A")
            members = [m.text for m in zone.findall(".//member") if m.text]
            member_str = ", ".join(members) if members else "(no members)"
            lines.append(f"  **{name}**: {member_str}")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo zones query failed")
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")


def get_route(destination: str) -> str:
    try:
        # Validate IP input
        try:
            ipaddress.ip_address(destination)
        except ValueError:
            return f"❌ Invalid IP address: `{destination}`\n\nUsage: `/palo route <ip>`"

        cmd = (
            f"<show><routing><fib><dst>{destination}</dst></fib></routing></show>"
        )
        resp = palo_op(cmd)
        root = ET.fromstring(resp.text)

        entries = root.findall(".//entry")
        if not entries:
            return (
                f"🔥 Route Lookup: {destination}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"No route found for {destination}."
            )

        lines = [f"🔥 Route Lookup: {destination}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for entry in entries[:3]:
            dst = _text(entry, "dst")
            nexthop = _text(entry, "nexthop")
            iface = _text(entry, "interface")
            metric = _text(entry, "metric")
            lines.append(f"Destination: {dst}")
            lines.append(f"Next hop:    {nexthop}")
            lines.append(f"Interface:   {iface}")
            lines.append(f"Metric:      {metric}")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo route lookup failed for %s", destination)
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")
