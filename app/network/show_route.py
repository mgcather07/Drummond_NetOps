# app/network/show_route.py
"""
TASK-012: /show ip route <device> <ip> — SSH show ip route lookup.
"""

import logging

from netmiko import ConnectHandler

from app.network.device_resolver import resolve_device

logger = logging.getLogger(__name__)


def show_ip_route(command: str) -> str:
    parts = command.split()
    if len(parts) < 5:
        return "Usage: `/show ip route <device> <ip>`"

    target, ip = parts[3], parts[4]

    try:
        device = resolve_device(target)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = conn.send_command(f"show ip route {ip}")
        conn.disconnect()

        if not output or "not in table" in output.lower():
            return f"📡 **{target}**: No route to `{ip}`."

        return f"📡 Route on **{target}** for `{ip}`\n\n{output[:2000]}"

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("show ip route failed on %s for %s", target, ip)
        return error(translate_exception(e), hint=f"Check that {target} ({host}) is reachable via SSH.")
