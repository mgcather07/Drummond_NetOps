from app.cucm.dial_plan import get_dial_plan_match, extract_likely_route_from_text
from app.cucm.route_pattern_details import (
    get_route_pattern_details,
    format_route_pattern_details,
)


def get_call_flow(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: /cucm call-flow <dialed number> from <site>"

    dialed_number = parts[2]

    route_command = command.replace("/cucm call-flow", "/cucm route", 1)

    dial_plan_result = get_dial_plan_match(route_command)
    likely_route = extract_likely_route_from_text(dial_plan_result)

    route_details = None

    if likely_route.get("found"):
        route_details = get_route_pattern_details(
            pattern=likely_route["pattern"],
            partition=likely_route["partition"],
        )

    outbound_trunk = "N/A"
    network_location = "N/A"
    discard_digits = "N/A"
    prefix_digits = "N/A"
    called_party_mask = "N/A"

    if route_details and route_details.get("found"):
        outbound_trunk = route_details.get("gateway", "N/A")
        network_location = route_details.get("network_location", "N/A")
        discard_digits = route_details.get("discard_digits", "N/A")
        prefix_digits = route_details.get("prefix_digits", "N/A")
        called_party_mask = route_details.get("called_party_transform_mask", "N/A")

    pattern = likely_route.get("pattern", "N/A")
    partition = likely_route.get("partition", "N/A")

    call_status = "✅ Call appears routable" if likely_route.get("found") else "❌ Call may not be routable"

    return f"""🧭 CUCM Call Flow Analysis

Dialed Number: {dialed_number}
Call Status: {call_status}

Summary:
The call matches a CUCM route pattern and appears to be able to leave through the configured outbound gateway or SIP trunk.

Outbound Path:
{outbound_trunk}

Network Location:
{network_location}

Technical Details:
Matched Route Pattern: {pattern}
Matched Partition: {partition}

Digit Manipulation:
Discard Digits: {discard_digits}
Prefix Digits Out: {prefix_digits}
Called Party Transform Mask: {called_party_mask}

Full Dial Plan Details:
{dial_plan_result}

✅ Call flow analysis completed."""