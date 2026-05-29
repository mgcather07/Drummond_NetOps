# app/palo/search.py
"""
TASK-019: Palo Alto address object lookup and security rule search by IP.

Commands:
  /palo search <ip>       — security rules referencing an IP (direct or via address object)
  /palo address <name>    — look up a named address object
"""

import ipaddress
import logging
import xml.etree.ElementTree as ET
from typing import Optional

from app.palo.client import palo_config_get

logger = logging.getLogger(__name__)

_DEVICE = "localhost.localdomain"
_VSYS = "vsys1"
_ADDR_XPATH = (
    f"/config/devices/entry[@name='{_DEVICE}']"
    f"/vsys/entry[@name='{_VSYS}']/address"
)
_RULES_XPATH = (
    f"/config/devices/entry[@name='{_DEVICE}']"
    f"/vsys/entry[@name='{_VSYS}']/rulebase/security/rules"
)


def _text(el, path: str, default: str = "N/A") -> str:
    node = el.find(path)
    return (node.text or default).strip() if node is not None else default


# ---------------------------------------------------------------------------
# Address object helpers
# ---------------------------------------------------------------------------

def _load_address_objects() -> dict:
    """
    Return dict: {object_name: {"type": ..., "value": ..., "networks": [ipaddress objects]}}
    """
    try:
        resp = palo_config_get(_ADDR_XPATH)
        root = ET.fromstring(resp.text)
        objects = {}
        for entry in root.findall(".//entry"):
            name = entry.get("name", "")
            ip_netmask = entry.find("ip-netmask")
            ip_range = entry.find("ip-range")
            fqdn = entry.find("fqdn")
            tags = [t.text for t in entry.findall(".//tag/member") if t.text]

            if ip_netmask is not None and ip_netmask.text:
                val = ip_netmask.text.strip()
                try:
                    nets = [ipaddress.ip_network(val, strict=False)]
                except ValueError:
                    nets = []
                objects[name] = {"type": "ip-netmask", "value": val, "networks": nets, "tags": tags}
            elif ip_range is not None and ip_range.text:
                val = ip_range.text.strip()
                objects[name] = {"type": "ip-range", "value": val, "networks": [], "range": val, "tags": tags}
            elif fqdn is not None and fqdn.text:
                val = fqdn.text.strip()
                objects[name] = {"type": "fqdn", "value": val, "networks": [], "tags": tags}

        return objects
    except Exception:
        logger.exception("Failed to load address objects")
        return {}


def _ip_in_object(ip: ipaddress.IPv4Address, obj: dict) -> bool:
    """Return True if ip falls within the address object."""
    if obj["type"] == "ip-netmask":
        return any(ip in net for net in obj.get("networks", []))
    if obj["type"] == "ip-range":
        try:
            start_str, end_str = obj["value"].split("-")
            start = ipaddress.ip_address(start_str.strip())
            end = ipaddress.ip_address(end_str.strip())
            return start <= ip <= end
        except Exception:
            return False
    return False  # fqdn — can't resolve at query time


def _members_match_ip(members: list, ip: ipaddress.IPv4Address, addr_objects: dict) -> tuple:
    """
    Given a list of rule member strings (direct IPs, CIDRs, or object names)
    and a target IP, return (matched: bool, reason: str).
    """
    for member in members:
        if member in ("any", "any-ipv4"):
            return True, "any"
        # Direct CIDR / IP
        try:
            net = ipaddress.ip_network(member, strict=False)
            if ip in net:
                return True, f"direct ({member})"
        except ValueError:
            pass
        # Address object lookup
        if member in addr_objects:
            if _ip_in_object(ip, addr_objects[member]):
                return True, f"{member} (address object)"
    return False, ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_address_object(name: str) -> str:
    try:
        addr_objects = _load_address_objects()
        # Case-insensitive search
        match = None
        for obj_name, obj in addr_objects.items():
            if obj_name.lower() == name.lower():
                match = (obj_name, obj)
                break

        if not match:
            return (
                f"❌ No address object named `{name}`\n\n"
                "Use `/palo search <ip>` to find rules referencing an IP."
            )

        obj_name, obj = match
        tag_str = ", ".join(obj.get("tags", [])) or "none"
        lines = [
            f"📦 Address Object: {obj_name}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Type:   {obj['type']}",
            f"Value:  {obj['value']}",
            f"Tags:   {tag_str}",
        ]
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo address object lookup failed for %s", name)
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")


def search_rules_by_ip(ip_str: str) -> str:
    try:
        # Validate IP
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return f"❌ Invalid IP address: `{ip_str}`\n\nUsage: `/palo search <ip>`"

        addr_objects = _load_address_objects()

        resp = palo_config_get(_RULES_XPATH)
        root = ET.fromstring(resp.text)

        matching = []
        for rule in root.findall(".//entry"):
            name = rule.get("name", "unknown")
            action = _text(rule, "action")

            src_members = [m.text for m in rule.findall(".//source/member") if m.text]
            dst_members = [m.text for m in rule.findall(".//destination/member") if m.text]

            src_match, src_reason = _members_match_ip(src_members, ip, addr_objects)
            dst_match, dst_reason = _members_match_ip(dst_members, ip, addr_objects)

            if src_match or dst_match:
                from_zone = ", ".join(m.text for m in rule.findall(".//from/member") if m.text) or "any"
                to_zone = ", ".join(m.text for m in rule.findall(".//to/member") if m.text) or "any"
                apps = ", ".join(m.text for m in rule.findall(".//application/member") if m.text) or "any"
                matching.append({
                    "name": name,
                    "action": action,
                    "from_zone": from_zone,
                    "to_zone": to_zone,
                    "apps": apps,
                    "src_reason": src_reason if src_match else "",
                    "dst_reason": dst_reason if dst_match else "",
                })

        if not matching:
            return (
                f"🔍 Rules referencing {ip_str}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "No security rules reference this IP."
            )

        MAX = 20
        lines = [
            f"🔍 Rules referencing {ip_str}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for r in matching[:MAX]:
            action_icon = "✅" if r["action"].lower() == "allow" else "❌"
            lines.append(f"{action_icon} **{r['name']}**")
            lines.append(f"   Zone:   {r['from_zone']} → {r['to_zone']}")
            if r["src_reason"]:
                lines.append(f"   Source: {r['src_reason']} ✓")
            if r["dst_reason"]:
                lines.append(f"   Dest:   {r['dst_reason']} ✓")
            lines.append(f"   App:    {r['apps']}")
            lines.append(f"   Action: {r['action']}")
            lines.append("")

        if len(matching) > MAX:
            lines.append(f"… {len(matching) - MAX} more rules not shown.")

        lines.append(f"{len(matching)} rule(s) found.")
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Palo rule search failed for %s", ip_str)
        return error(translate_exception(e), hint="Check PALO_HOST and PALO_API_KEY in .env.")
