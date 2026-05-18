from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport
from zeep.helpers import serialize_object
from zeep import Client, Settings
from app.cucm.trunk_status import get_trunk_status

from app.data.trunks import get_trunk

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def get_sip_trunk(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: /cucm trunk <trunk alias>"

    trunk_input = parts[2]
    trunk = get_trunk(trunk_input)

    if not trunk:
        return f"❌ Unknown trunk: {trunk_input}"

    trunk_name = trunk["name"]

    try:
        axl_url = f"https://{CUCM_HOST}:8443/axl/"

        session = requests.Session()
        session.verify = False
        session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

        transport = Transport(session=session, timeout=20)

        settings = Settings(strict=False, xml_huge_tree=True)

        client = Client(
            wsdl="schema/15.0/AXLAPI.wsdl",
            transport=transport,
            settings=settings
        )

        service = client.create_service(
            "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
            axl_url
        )

        response = service.getSipTrunk(name=trunk_name)
        sip_trunk = serialize_object(response["return"]["sipTrunk"])

        description = sip_trunk.get("description", "N/A")

        device_pool = "N/A"
        if sip_trunk.get("devicePoolName"):
            device_pool = sip_trunk["devicePoolName"].get("_value_1", "N/A")

        css = "N/A"
        if sip_trunk.get("callingSearchSpaceName"):
            css = sip_trunk["callingSearchSpaceName"].get("_value_1", "N/A")

        location = "N/A"
        if sip_trunk.get("locationName"):
            location = sip_trunk["locationName"].get("_value_1", "N/A")

        security_profile = "N/A"
        if sip_trunk.get("securityProfileName"):
            security_profile = sip_trunk["securityProfileName"].get("_value_1", "N/A")

        sip_profile = "N/A"
        if sip_trunk.get("sipProfileName"):
            sip_profile = sip_trunk["sipProfileName"].get("_value_1", "N/A")

        destinations_text = "No destinations found"
        destinations = sip_trunk.get("destinations")

        if destinations and destinations.get("destination"):
            dest_list = destinations["destination"]

            if not isinstance(dest_list, list):
                dest_list = [dest_list]

            formatted_destinations = []

            for dest in dest_list:
                address = dest.get("addressIpv4") or dest.get("addressIpv6") or "N/A"
                port = dest.get("port", "N/A")
                sort_order = dest.get("sortOrder", "N/A")
                formatted_destinations.append(f"• {address}:{port}  Order: {sort_order}")

            destinations_text = "\n".join(formatted_destinations)
            status_info = get_trunk_status(trunk_name)

        return f"""📡 SIP Trunk Lookup: {trunk_name}

Friendly Name: {trunk["key"]}
Site: {trunk.get("site", "N/A")}
Provider: {trunk.get("provider", "N/A")}
Type: {trunk.get("type", "N/A")}

Description: {description}
Device Pool: {device_pool}
Calling Search Space: {css}
Location: {location}

Security Profile: {security_profile}
SIP Profile: {sip_profile}

Destinations:
{destinations_text}

Live Status
Status: {status_info.get("status", "N/A")}
Active Node: {status_info.get("active_node", "N/A")}
Protocol: {status_info.get("protocol", "N/A")}

✅ SIP trunk AXL + RISPort lookup successful."""

    except Exception as e:
        return f"""❌ SIP trunk lookup failed.

Trunk Input: {trunk_input}
Resolved Name: {trunk_name}

Error Type: {type(e).__name__}
Error:
{str(e)}"""