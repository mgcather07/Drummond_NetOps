# app/palo/policy.py
"""
TASK-010: Palo Alto policy match and NAT lookup.

Commands:
  /palo policy <src> <dst> <port>  — test security-policy-match
  /palo nat <ip>                   — test NAT policy match
"""

import logging
import xml.etree.ElementTree as ET

from app.palo.client import palo_op

logger = logging.getLogger(__name__)


def _text(el, path: str, default: str = "N/A") -> str:
    node = el.find(path)
    return (node.text or default).strip() if node is not None else default


def get_policy_match(src: str, dst: str, port: str) -> str:
    """
    Run 'test security-policy-match' on the firewall and return a
    formatted summary of matching rules.
    """
    try:
        # Port can be a number or service name; protocol defaults to tcp
        protocol = "6"  # TCP
        if "/" in port:
            proto_str, port = port.split("/", 1)
            protocol = "6" if proto_str.lower() == "tcp" else "17"

        cmd = (
            f"<test><security-policy-match>"
            f"<source>{src}</source>"
            f"<destination>{dst}</destination>"
            f"<destination-port>{port}</destination-port>"
            f"<protocol>{protocol}</protocol>"
            f"</security-policy-match></test>"
        )
        resp = palo_op(cmd)
        root = ET.fromstring(resp.text)

        rules = root.findall(".//rules/entry")
        if not rules:
            # Try alternate response shape
            rules = root.findall(".//entry")

        if not rules:
            return (
                f"🔥 Policy Match: {src} → {dst}:{port}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "No matching security rule found.\n"
                "Traffic would be denied by default."
            )

        lines = [
            f"🔥 Policy Match: {src} → {dst}:{port}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for rule in rules[:5]:  # cap at 5
            name = rule.get("name", "unknown")
            action = _text(rule, "action", "unknown")
            action_icon = "✅" if action.lower() == "allow" else "❌"
            from_zone = _text(rule, "from/member", _text(rule, "from"))
            to_zone = _text(rule, "to/member", _text(rule, "to"))
            lines.append(f"{action_icon} Rule: **{name}**")
            lines.append(f"   Zone:   {from_zone} → {to_zone}")
            lines.append(f"   Action: {action}")
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo policy match failed (%s → %s:%s)", src, dst, port)
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")


def get_nat_match(ip: str) -> str:
    """
    Run 'test nat-policy-match' for a source IP and return matching NAT rules.
    """
    try:
        cmd = (
            f"<test><nat-policy-match>"
            f"<source>{ip}</source>"
            f"<destination>any</destination>"
            f"<destination-port>0</destination-port>"
            f"<protocol>6</protocol>"
            f"</nat-policy-match></test>"
        )
        resp = palo_op(cmd)
        root = ET.fromstring(resp.text)

        rules = root.findall(".//rules/entry") or root.findall(".//entry")
        if not rules:
            return (
                f"🔥 NAT Match: {ip}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"No NAT rule matches traffic from {ip}."
            )

        lines = [f"🔥 NAT Match: {ip}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for rule in rules[:5]:
            name = rule.get("name", "unknown")
            nat_type = _text(rule, "nat-type", "unknown")
            translated_src = _text(rule, "source-translation/translated-address", "")
            lines.append(f"  Rule: **{name}**")
            lines.append(f"  Type: {nat_type}")
            if translated_src:
                lines.append(f"  Translated to: {translated_src}")
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo NAT match failed for %s", ip)
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")
