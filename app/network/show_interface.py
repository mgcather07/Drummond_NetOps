# app/network/show_interface.py
"""
TASK-012: /show interface <device> <iface> — SSH show interfaces detail.
"""

import logging

from netmiko import ConnectHandler

from app.network.device_resolver import resolve_device

logger = logging.getLogger(__name__)


def show_interface(command: str) -> str:
    parts = command.split()
    if len(parts) < 4:
        return "Usage: `/show interface <device> <interface>`"

    target, iface = parts[2], parts[3]

    try:
        device = resolve_device(target)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = conn.send_command(f"show interfaces {iface}")
        conn.disconnect()

        if not output or "Invalid" in output:
            return f"❌ Interface `{iface}` not found on {target}."

        return f"🔌 **{target}** `{iface}`\n\n{output[:3000]}"

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("show interface failed on %s for %s", target, iface)
        return error(translate_exception(e), hint=f"Check that {target} ({host}) is reachable via SSH.")
