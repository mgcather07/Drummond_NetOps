# app/network/vlan.py
"""
TASK-023: VLAN info and port membership.

Commands:
  /net vlan <device>           — VLAN brief list
  /net vlan <device> <vlan-id> — ports in a specific VLAN
  /net port <device> <iface>   — VLAN membership for a port
"""

import logging
import re
from typing import Optional

from netmiko import ConnectHandler

from app.network.device_resolver import resolve_device

logger = logging.getLogger(__name__)


def get_vlans(device_name: str, vlan_id: Optional[str] = None) -> str:
    try:
        device = resolve_device(device_name)
    except ValueError as e:
        return str(e)

    if vlan_id is not None:
        try:
            vlan_num = int(vlan_id)
            if not (1 <= vlan_num <= 4094):
                return f"❌ Invalid VLAN ID: `{vlan_id}` — must be 1–4094."
        except ValueError:
            return f"❌ Invalid VLAN ID: `{vlan_id}` — must be a number."

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})

        if vlan_id:
            output = conn.send_command(f"show vlan id {vlan_id}")
        else:
            output = conn.send_command("show vlan brief")
        conn.disconnect()

        if "VLAN not found" in output or "not found" in output.lower():
            return f"📋 VLAN {vlan_id} on {device_name}\n━━━━━━━━━━━━━━━━━━━━━━━\nVLAN {vlan_id} not found."

        # Parse the output into lines
        lines_out = [
            f"📋 {'VLAN ' + vlan_id if vlan_id else 'VLANs'} on {device_name}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for line in output.splitlines():
            # Skip header/separator lines
            if not line.strip() or line.startswith("-") or line.startswith("VLAN"):
                if "VLAN" in line and "Name" in line:
                    lines_out.append(line)  # keep header
                continue
            lines_out.append(line)

        return "\n".join(lines_out)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("VLAN query failed on %s", device_name)
        return error(translate_exception(e), hint=f"Check that {device_name} ({host}) is reachable.")


def get_port_vlan(device_name: str, interface: str) -> str:
    try:
        device = resolve_device(device_name)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = conn.send_command(f"show interfaces {interface} switchport")
        conn.disconnect()

        if not output or "Invalid" in output or "%" in output[:20]:
            return f"❌ Interface `{interface}` not found on {device_name}."

        # Parse key fields
        fields = {}
        for line in output.splitlines():
            for label in ("Administrative Mode", "Operational Mode",
                          "Access Mode VLAN", "Voice VLAN",
                          "Trunking Native Mode VLAN",
                          "Trunking VLANs Enabled"):
                if line.strip().startswith(label):
                    fields[label] = line.split(":", 1)[-1].strip()

        lines_out = [
            f"🔌 Port Info: {device_name} {interface}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for label, val in fields.items():
            lines_out.append(f"{label:<32} {val}")

        return "\n".join(lines_out)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Port VLAN query failed on %s for %s", device_name, interface)
        return error(translate_exception(e), hint=f"Check that {device_name} ({host}) is reachable.")
