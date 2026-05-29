# app/network/stats.py
"""
TASK-024: Interface error and utilization stats.

Command:
  /net stats <device> <interface>  — error counters, rates, link state
"""

import logging
import re

from netmiko import ConnectHandler

from app.network.device_resolver import resolve_device

logger = logging.getLogger(__name__)

_WARN_CRC = 0       # any CRC errors → warn
_WARN_DROPS = 100   # > 100 drops → warn


def _flag(value: int, threshold: int) -> str:
    return " ⚠️" if value > threshold else ""


def _parse_int(text: str) -> int:
    try:
        return int(text.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def get_interface_stats(device_name: str, interface: str) -> str:
    try:
        device = resolve_device(device_name)
    except ValueError as e:
        return str(e)

    host = device["host"]
    try:
        conn = ConnectHandler(**{k: v for k, v in device.items() if k != "name"})
        output = conn.send_command(f"show interfaces {interface}")
        conn.disconnect()

        if not output or "Invalid" in output or "%" in output[:20]:
            return f"❌ Interface `{interface}` not found on {device_name}."

        # --- State line ---
        admin_state, proto_state = "unknown", "unknown"
        m = re.search(r"(\S+) is (\S+),\s+line protocol is (\S+)", output)
        if m:
            admin_state = m.group(2).rstrip(",")
            proto_state = m.group(3).rstrip(",")
        state_str = f"{admin_state} / line protocol {proto_state}"
        state_icon = "✅" if proto_state == "up" else "❌"

        # --- Speed/duplex ---
        speed, duplex = "N/A", "N/A"
        m = re.search(r"BW\s+(\d+)\s+Kbit", output)
        if m:
            bw_kbps = int(m.group(1))
            speed = f"{bw_kbps // 1000} Mbps" if bw_kbps >= 1000 else f"{bw_kbps} Kbps"
        m = re.search(r"(Full|Half)-duplex", output, re.IGNORECASE)
        if m:
            duplex = m.group(0)
        duplex_warn = " ⚠️" if "half" in duplex.lower() else ""

        # --- Input/output rates ---
        in_rate, out_rate = "N/A", "N/A"
        m = re.search(r"5 minute input rate\s+(\d[\d,]*)\s+bits", output)
        if m:
            in_rate = f"{int(m.group(1).replace(',','')):,} bps"
        m = re.search(r"5 minute output rate\s+(\d[\d,]*)\s+bits", output)
        if m:
            out_rate = f"{int(m.group(1).replace(',','')):,} bps"

        # --- Error counters ---
        input_errs = crc_errs = input_drops = output_drops = 0
        m = re.search(r"(\d[\d,]*)\s+input errors", output)
        if m:
            input_errs = _parse_int(m.group(1))
        m = re.search(r"(\d[\d,]*)\s+CRC", output)
        if m:
            crc_errs = _parse_int(m.group(1))
        m = re.search(r"(\d[\d,]*)\s+input drops", output)
        if m:
            input_drops = _parse_int(m.group(1))
        m = re.search(r"(\d[\d,]*)\s+output drops", output)
        if m:
            output_drops = _parse_int(m.group(1))

        # --- Last clearing ---
        last_clear = "never"
        m = re.search(r'Last clearing.*?"show interface".*?counters\s+(.*)', output)
        if m:
            last_clear = m.group(1).strip()

        lines = [
            f"📊 Interface Stats: {device_name} {interface}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"State:         {state_icon} {state_str}",
            f"Speed:         {speed}, {duplex}{duplex_warn}",
            "",
            f"Input rate:    {in_rate}",
            f"Output rate:   {out_rate}",
            "",
            f"Input errors:  {input_errs:,}",
            f"CRC errors:    {crc_errs:,}{_flag(crc_errs, _WARN_CRC)}",
            f"Input drops:   {input_drops:,}{_flag(input_drops, _WARN_DROPS)}",
            f"Output drops:  {output_drops:,}{_flag(output_drops, _WARN_DROPS)}",
            "",
            f"Last cleared:  {last_clear}",
        ]
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Interface stats failed on %s for %s", device_name, interface)
        return error(translate_exception(e), hint=f"Check that {device_name} ({host}) is reachable.")
