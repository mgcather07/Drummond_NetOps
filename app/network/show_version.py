import logging

from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()
logger = logging.getLogger(__name__)


def show_version(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: `/show version <device-name-or-ip>`"

    target = parts[2]

    try:
        from app.network.device_resolver import resolve_device
        device = resolve_device(target)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        connection = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = connection.send_command("show version")
        connection.disconnect()

        return (
            f"✅ Connected to **{target}** ({host})\n\n"
            f"{output[:3000]}"
        )

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("show version failed for %s (%s)", target, host)
        return error(translate_exception(e), hint=f"Check that {target} ({host}) is reachable via SSH.")
