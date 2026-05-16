# app/network/ping.py
import subprocess


def ping_host(command: str) -> str:
    parts = command.split()

    if len(parts) < 2:
        return "Usage: /ping <ip or hostname>"

    target = parts[1]

    try:
        result = subprocess.run(
            ["ping", "-c", "4", target],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return f"""
✅ Ping Successful: {target}

{result.stdout}
"""

        return f"""
❌ Ping Failed: {target}

{result.stderr or result.stdout}
"""

    except Exception as e:
        return f"Error running ping: {str(e)}"