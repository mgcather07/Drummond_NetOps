# app/network/neighbors.py
"""
TASK-022: CDP / LLDP neighbor discovery.

Commands:
  /net neighbors <device>             — all neighbors
  /net neighbors <device> <interface> — specific port detail
"""

import logging
import re
from typing import Optional

from netmiko import ConnectHandler

from app.network.device_resolver import resolve_device

logger = logging.getLogger(__name__)


def _parse_cdp_detail(raw: str) -> list:
    """Parse 'show cdp neighbors detail' into a list of neighbor dicts."""
    neighbors = []
    # Split on the dashed separator line between entries
    blocks = re.split(r"-{10,}", raw)
    for block in blocks:
        if not block.strip():
            continue
        entry = {}
        m = re.search(r"Device ID:\s*(.+)", block)
        if m:
            entry["device_id"] = m.group(1).strip()
        m = re.search(r"IP address:\s*(\S+)", block, re.IGNORECASE)
        if m:
            entry["ip"] = m.group(1).strip()
        m = re.search(r"Interface:\s*(\S+),\s*Port ID.*?:\s*(\S+)", block)
        if m:
            entry["local_iface"] = m.group(1).strip()
            entry["remote_iface"] = m.group(2).strip()
        m = re.search(r"Platform:\s*(.+?),", block)
        if m:
            entry["platform"] = m.group(1).strip()
        if entry.get("device_id"):
            neighbors.append(entry)
    return neighbors


def _parse_lldp_detail(raw: str) -> list:
    """Parse 'show lldp neighbors detail' into a list of neighbor dicts."""
    neighbors = []
    blocks = re.split(r"-{10,}", raw)
    for block in blocks:
        if not block.strip():
            continue
        entry = {}
        m = re.search(r"System Name:\s*(.+)", block)
        if m:
            entry["device_id"] = m.group(1).strip()
        m = re.search(r"Management Addresses.*?(\d+\.\d+\.\d+\.\d+)", block, re.DOTALL)
        if m:
            entry["ip"] = m.group(1).strip()
        m = re.search(r"Local Intf:\s*(\S+)", block)
        if m:
            entry["local_iface"] = m.group(1).strip()
        m = re.search(r"Port id:\s*(\S+)", block)
        if m:
            entry["remote_iface"] = m.group(1).strip()
        m = re.search(r"System Description:\s*(.+?)(?:\n[A-Z]|\Z)", block, re.DOTALL)
        if m:
            entry["platform"] = m.group(1).strip()[:60]
        if entry.get("device_id"):
            neighbors.append(entry)
    return neighbors


def get_neighbors(device_name: str, interface: Optional[str] = None) -> str:
    try:
        device = resolve_device(device_name)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})

        # Try CDP first
        cmd = f"show cdp neighbors{' ' + interface if interface else ''} detail"
        raw = conn.send_command(cmd, read_timeout=60)

        protocol = "CDP"
        neighbors = _parse_cdp_detail(raw)

        # Fall back to LLDP if CDP returns nothing
        if not neighbors or "CDP is not enabled" in raw or "not enabled" in raw.lower():
            lldp_cmd = f"show lldp neighbors{' ' + interface if interface else ''} detail"
            raw = conn.send_command(lldp_cmd, read_timeout=60)
            neighbors = _parse_lldp_detail(raw)
            protocol = "LLDP"

        conn.disconnect()

        if not neighbors:
            return (
                f"📡 Neighbors on {device_name}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "No CDP or LLDP neighbors found."
            )

        MAX = 20
        title = f"📡 {protocol} Neighbors on {device_name}"
        if interface:
            title += f" {interface}"
        lines = [title, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        if interface:
            # Detail mode — one neighbor expected
            n = neighbors[0]
            lines += [
                f"Device ID:    {n.get('device_id', 'N/A')}",
                f"Local port:   {n.get('local_iface', 'N/A')}",
                f"Remote port:  {n.get('remote_iface', 'N/A')}",
                f"Platform:     {n.get('platform', 'N/A')}",
                f"IP address:   {n.get('ip', 'N/A')}",
            ]
        else:
            # Summary table
            lines.append(f"{'Local Port':<20} {'Remote Device':<24} {'Remote Port':<20} {'IP'}")
            lines.append(f"{'─'*20} {'─'*24} {'─'*20} {'─'*15}")
            for n in neighbors[:MAX]:
                lines.append(
                    f"{n.get('local_iface','N/A'):<20} "
                    f"{n.get('device_id','N/A'):<24} "
                    f"{n.get('remote_iface','N/A'):<20} "
                    f"{n.get('ip','N/A')}"
                )
            if len(neighbors) > MAX:
                lines.append(f"… {len(neighbors) - MAX} more neighbors not shown.")
            lines.append(f"\n{len(neighbors)} neighbor(s) found (via {protocol}).")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("CDP/LLDP neighbor query failed on %s", device_name)
        return error(translate_exception(e), hint=f"Check that {device_name} ({host}) is reachable.")
