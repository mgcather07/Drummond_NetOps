import requests

from app.cucm.route_plan import get_used_route_plan_patterns
from app.cucm.trunk_status import get_trunk_status
from app.cucm.dbreplication import get_dbreplication_status
from app.data.trunks import TRUNKS
from app.data.cucm_nodes import CUCM_NODES

requests.packages.urllib3.disable_warnings()


def check_node_reachable(ip: str) -> bool:
    try:
        response = requests.get(
            f"https://{ip}",
            verify=False,
            timeout=5
        )

        return response.status_code in [200, 301, 302, 401, 403]

    except Exception:
        return False


def get_cucm_health(command: str) -> str:
    axl_status = "❌ Failed"
    dbreplication_status = "⚠️ Not Checked"
    route_plan_count = 0

    trunk_registered = 0
    trunk_not_registered = 0
    trunk_errors = 0

    healthy_nodes = 0
    failed_nodes = 0

    trunk_lines = []
    node_lines = []

    #
    # AXL / Route Plan Health
    #

    try:
        used_patterns = get_used_route_plan_patterns()
        route_plan_count = len(used_patterns)
        axl_status = "✅ Responding"

    except Exception as e:
        logger.exception("AXL health check failed")
        axl_status = "❌ Failed — could not reach CUCM AXL"

    #
    # Database Replication Health
    #

    dbreplication_summary = ""

    try:
        dbreplication = get_dbreplication_status()
        dbreplication_status = dbreplication.get("status", "N/A")
        dbreplication_summary = dbreplication.get(
            "summary",
            f"Database Replication: {dbreplication_status}"
        )

    except Exception as e:
        logger.exception("DB replication health check failed")
        dbreplication_status = "❌ Failed — SSH or DB error"
        dbreplication_summary = f"Database Replication: {dbreplication_status}"

    #
    # SIP Trunk Health
    #

    for trunk_key, trunk_data in TRUNKS.items():
        trunk_name = trunk_data.get("name", trunk_key)

        status_info = get_trunk_status(trunk_name)

        status = status_info.get("status", "Unknown")
        active_node = status_info.get("active_node", "N/A")

        if status.lower() == "registered":
            trunk_registered += 1
            icon = "✅"

        elif "error" in status.lower():
            trunk_errors += 1
            icon = "❌"

        else:
            trunk_not_registered += 1
            icon = "⚠️"

        trunk_lines.append(
            f"{icon} {trunk_key}: {status} | Node: {active_node}"
        )

    #
    # Node Health
    #

    for node in CUCM_NODES:
        node_type = node.get("name", "Node")
        hostname = node.get("hostname", "Unknown")
        ip = node.get("ip", "Unknown")
        site = node.get("site", "Unknown")

        reachable = check_node_reachable(ip)

        if reachable:
            healthy_nodes += 1
            icon = "✅"
            status = "Reachable"

        else:
            failed_nodes += 1
            icon = "❌"
            status = "Unreachable"

        node_lines.append(
            f"{icon} {node_type} - {hostname} ({site}) | {ip} | {status}"
        )

    #
    # Overall Health
    #

    if (
            axl_status.startswith("✅")
            and dbreplication_status.startswith("✅")
            and trunk_not_registered == 0
            and trunk_errors == 0
            and failed_nodes == 0
    ):
        overall = "✅ Healthy"

    elif (
            axl_status.startswith("❌")
            or dbreplication_status.startswith("❌")
            or trunk_errors > 0
            or failed_nodes > 0
    ):
        overall = "🔴 Critical"

    else:
        overall = "🟡 Warning"

    trunk_summary = "\n".join(trunk_lines) if trunk_lines else "No trunks configured."
    node_summary = "\n".join(node_lines) if node_lines else "No CUCM nodes configured."

    return f"""🏥 CUCM Health Summary

Overall Status: {overall}

AXL Status: {axl_status}

{dbreplication_summary}

Route Plan Objects Checked: {route_plan_count}

CUCM Node Health:
Healthy Nodes: {healthy_nodes}
Failed Nodes: {failed_nodes}

{node_summary}

SIP Trunk Health:
Registered: {trunk_registered}
Warning/Not Registered: {trunk_not_registered}
Errors: {trunk_errors}

Configured Trunks:
{trunk_summary}

✅ CUCM health check completed."""
