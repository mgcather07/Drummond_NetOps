# app/network/traceroute.py
"""
TASK-012: /traceroute command — runs system traceroute.
"""

import logging
import subprocess

logger = logging.getLogger(__name__)


def traceroute_host(command: str) -> str:
    parts = command.split()
    if len(parts) < 2:
        return "Usage: `/traceroute <ip-or-hostname>`"

    target = parts[1]
    try:
        result = subprocess.run(
            ["traceroute", "-m", "15", "-w", "2", target],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout or result.stderr
        if not output.strip():
            return f"❌ No output from traceroute to {target}."

        return f"🔍 Traceroute to **{target}**\n\n{output[:3000]}"

    except subprocess.TimeoutExpired:
        return f"❌ Traceroute to {target} timed out after 60 seconds."
    except FileNotFoundError:
        return "❌ `traceroute` command not available on this host."
    except Exception as e:
        from app.utils.responses import error
        logger.exception("Traceroute failed for %s", target)
        return error("Traceroute failed", hint=f"Could not run traceroute to {target}.")
