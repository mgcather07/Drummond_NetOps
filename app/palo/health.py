# app/palo/health.py
"""
TASK-017: Palo Alto system health and HA state.

Commands:
  /palo health  — CPU, memory, sessions, uptime
  /palo ha      — HA pair state, sync status
"""

import logging
import xml.etree.ElementTree as ET

from app.palo.client import palo_op

logger = logging.getLogger(__name__)


def _text(el, path: str, default: str = "N/A") -> str:
    node = el.find(path)
    return (node.text or default).strip() if node is not None else default


def get_system_health() -> str:
    try:
        resp = palo_op("<show><system><resources/></system></show>")
        root = ET.fromstring(resp.text)

        # The response is typically a <response><result> block containing
        # a plain-text "top"-style output; parse the key values from it.
        result_text = ""
        result_node = root.find(".//result")
        if result_node is not None and result_node.text:
            result_text = result_node.text.strip()

        # Also try the structured system info for uptime/version
        info_resp = palo_op("<show><system><info/></system></show>")
        info_root = ET.fromstring(info_resp.text)
        info = info_root.find(".//result/system")

        uptime = _text(info, "uptime") if info is not None else "N/A"
        hostname = _text(info, "hostname") if info is not None else "N/A"
        version = _text(info, "sw-version") if info is not None else "N/A"
        model = _text(info, "model") if info is not None else "N/A"

        # Session info
        sess_resp = palo_op("<show><session><info/></session></show>")
        sess_root = ET.fromstring(sess_resp.text)
        sess_info = sess_root.find(".//result")
        active_sess = _text(sess_info, "num-active") if sess_info is not None else "N/A"
        max_sess = _text(sess_info, "num-max") if sess_info is not None else "N/A"

        lines = [
            "🔥 Palo Alto System Health",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Hostname:  {hostname}",
            f"Model:     {model}",
            f"PAN-OS:    {version}",
            f"Uptime:    {uptime}",
            "",
            f"Sessions:  {active_sess} active / {max_sess} max",
        ]

        # Include the top-style resource text if present (CPU/mem)
        if result_text:
            # Extract just the CPU/Mem lines from the top output
            for line in result_text.splitlines():
                if any(kw in line.lower() for kw in ("cpu", "mem", "load")):
                    lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo health check failed")
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")


def get_ha_state() -> str:
    try:
        resp = palo_op("<show><high-availability><state/></high-availability></show>")
        root = ET.fromstring(resp.text)
        result = root.find(".//result")

        if result is None:
            return "🔥 Palo Alto HA\n━━━━━━━━━━━━━━━━━━━━━━━━\nCould not retrieve HA state."

        enabled = _text(result, "enabled")
        if enabled.lower() == "no":
            return (
                "🔥 Palo Alto HA\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "HA is not enabled on this firewall."
            )

        local = result.find("group/local-info")
        peer = result.find("group/peer-info")
        running_sync = _text(result, "group/running-sync")

        local_state = _text(local, "state") if local is not None else "N/A"
        peer_state = _text(peer, "state") if peer is not None else "N/A"
        peer_conn = _text(peer, "conn-status") if peer is not None else "N/A"
        last_sync = _text(result, "group/running-sync-check")

        sync_icon = "✅" if "synchronized" in running_sync.lower() else "⚠️"
        peer_icon = "✅" if peer_conn.lower() == "up" else "❌"

        lines = [
            "🔥 Palo Alto HA State",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Local state:    {local_state}",
            f"Peer state:     {peer_state}",
            f"Peer conn:      {peer_icon} {peer_conn}",
            f"Config sync:    {sync_icon} {running_sync}",
        ]
        if last_sync and last_sync != "N/A":
            lines.append(f"Last sync check: {last_sync}")
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo HA state check failed")
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")
