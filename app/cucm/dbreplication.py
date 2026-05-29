from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)
import os
import time
import re
from netmiko import ConnectHandler
from typing import Optional
from app.data.cucm_nodes import CUCM_NODES

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_SSH_USERNAME = os.getenv("CUCM_SSH_USERNAME")
CUCM_SSH_PASSWORD = os.getenv("CUCM_SSH_PASSWORD")


def get_friendly_node_name(replication_state: str, server: str) -> str:
    for node in CUCM_NODES:
        if str(node.get("replication_state")) == str(replication_state):
            return node.get("friendly_name") or node.get("hostname") or server

    return server

def read_until_prompt(connection, max_wait_seconds: int = 90) -> str:
    output = ""
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        chunk = connection.read_channel()

        if chunk:
            output += chunk

            if output.strip().endswith("admin:"):
                break

        time.sleep(2)

    return output


def parse_replication_nodes(detail_output: str) -> list[dict]:
    """
    Parses lines like:

    g_2_ccm15_0_1_12900_234  2 Active  Local      0
    g_4_ccm15_0_1_12900_234  4 Active  Connected  0 Feb 21 19:00:40
    """

    nodes = []

    for line in detail_output.splitlines():
        line = line.strip()

        if not line.startswith("g_"):
            continue

        parts = line.split()

        if len(parts) < 5:
            continue

        server = parts[0]
        state = parts[1]
        status = parts[2]
        connection = parts[3]
        queue = parts[4]

        changed = " ".join(parts[5:]) if len(parts) > 5 else "N/A"

        nodes.append({
            "server": server,
            "state": state,
            "status": status,
            "connection": connection,
            "queue": queue,
            "changed": changed,
        })

    return nodes

def build_replication_summary(status: str, detail_command: Optional[str], detail_output: str) -> str:
    nodes = parse_replication_nodes(detail_output)

    active_nodes = 0
    queue_warnings = 0
    bad_nodes = 0

    node_lines = []

    for node in nodes:
        node_status = node["status"]
        connection = node["connection"]
        queue = node["queue"]

        is_active = node_status.lower() == "active"
        is_connected = connection.lower() in ["local", "connected"]
        queue_ok = queue == "0"

        if is_active and is_connected and queue_ok:
            icon = "✅"
            active_nodes += 1
        else:
            icon = "⚠️"
            bad_nodes += 1

        if not queue_ok:
            queue_warnings += 1

        friendly_name = get_friendly_node_name(
            replication_state=node["state"],
            server=node["server"]
        )

        node_lines.append(
            f"{icon} {friendly_name} | {connection} | Queue: {queue}"
        )

    if not node_lines:
        node_lines.append("⚠️ No replication node detail parsed.")

    summary_lines = [
        f"Database Replication: {status}",
        "",
        "Replication Summary:",
        f"✅ Nodes Active: {active_nodes}",
        f"{'✅' if queue_warnings == 0 else '⚠️'} Queue Warnings: {queue_warnings}",
        f"{'✅' if bad_nodes == 0 else '⚠️'} Problem Nodes: {bad_nodes}",
        "",
        "Nodes:",
        *node_lines,
    ]

    if detail_command:
        summary_lines.extend([
            "",
            "Detail Log:",
            detail_command
        ])

    return "\n".join(summary_lines)


def get_dbreplication_status() -> dict:
    connection = None

    detail_command = None
    detail_output = ""
    clean_output = ""

    try:
        device = {
            "device_type": "generic",
            "host": CUCM_HOST,
            "username": CUCM_SSH_USERNAME,
            "password": CUCM_SSH_PASSWORD,
            "port": 22,
        }

        connection = ConnectHandler(**device)
        connection.find_prompt()

        connection.write_channel("utils dbreplication runtimestate\n")

        output = read_until_prompt(
            connection=connection,
            max_wait_seconds=120
        )

        clean_output = output.strip()
        output_lower = clean_output.lower()

        match = re.search(r"'(file view activelog[^']+)'", clean_output)

        if match:
            detail_command = match.group(1)

            connection.write_channel(f"{detail_command}\n")

            detail_output = read_until_prompt(
                connection=connection,
                max_wait_seconds=90
            ).strip()

        if "errors or data mismatches were found" in output_lower:
            if "(2) setup completed" in output_lower and "y/y/y" in output_lower:
                status = "🟡 Warning - Previous mismatch detected"
            else:
                status = "❌ Bad - Replication mismatch detected"

        elif "(2) setup completed" in output_lower and "y/y/y" in output_lower:
            status = "✅ Good"

        else:
            status = "⚠️ Review Required"

        clean_summary = build_replication_summary(
            status=status,
            detail_command=detail_command,
            detail_output=detail_output
        )

        return {
            "status": status,
            "summary": clean_summary,
            "output": clean_output,
            "detail_command": detail_command,
            "detail_output": detail_output,
            "nodes": parse_replication_nodes(detail_output),
            "error": None,
        }

    except Exception as e:
        return {
            "status": f"❌ Failed - {type(e).__name__}: {str(e)}",
            "summary": f"Database Replication: ❌ Failed - {type(e).__name__}: {str(e)}",
            "output": clean_output,
            "detail_command": detail_command,
            "detail_output": detail_output,
            "nodes": [],
            "error": str(e),
        }

    finally:
        if connection:
            connection.disconnect()