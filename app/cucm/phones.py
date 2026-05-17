from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
from app.cucm.risport import get_phone_status

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def get_phone(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: /cucm phone <SEP device name>"

    phone_name = parts[2].upper()

    if not phone_name.startswith("SEP"):
        phone_name = f"SEP{phone_name}"

    if not CUCM_HOST or not CUCM_USERNAME or not CUCM_PASSWORD:
        return "❌ CUCM environment variables are missing. Check CUCM_HOST, CUCM_USERNAME, and CUCM_PASSWORD."

    try:
        axl_url = f"https://{CUCM_HOST}:8443/axl/"

        session = requests.Session()
        session.verify = False
        session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

        transport = Transport(session=session, timeout=10)

        client = Client(
            wsdl="schema/15.0/AXLAPI.wsdl",
            transport=transport
        )

        service = client.create_service(
            "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
            axl_url
        )

        response = service.getPhone(name=phone_name)
        phone = serialize_object(response["return"]["phone"])

        description = phone.get("description", "N/A")

        device_pool = "N/A"
        if phone.get("devicePoolName"):
            device_pool = phone["devicePoolName"].get("_value_1", "N/A")

        css = "N/A"
        if phone.get("callingSearchSpaceName"):
            css = phone["callingSearchSpaceName"].get("_value_1", "N/A")

        location = "N/A"
        if phone.get("locationName"):
            location = phone["locationName"].get("_value_1", "N/A")

        lines_text = "No lines found"

        lines = phone.get("lines")
        if lines and lines.get("line"):
            phone_lines = lines["line"]

            if not isinstance(phone_lines, list):
                phone_lines = [phone_lines]

            formatted_lines = []

            for item in phone_lines:
                line_info = item.get("dirn", {})
                pattern = line_info.get("pattern", "N/A")
                partition = line_info.get("routePartitionName", "N/A")

                if isinstance(partition, dict):
                    partition = partition.get("_value_1", "N/A")

                formatted_lines.append(f"• {pattern} / {partition}")

            lines_text = "\n".join(formatted_lines)

        status_info = get_phone_status(phone_name)

        return f"""📞 CUCM Phone Lookup: {phone_name}

Description: {description}
Device Pool: {device_pool}
Calling Search Space: {css}
Location: {location}

Lines:
{lines_text}

Live Status
Registration: {status_info.get("status", "N/A")}
IP Address: {status_info.get("ip_address", "N/A")}
Active Node: {status_info.get("active_node", "N/A")}
Model: {status_info.get("model", "N/A")}
Firmware: {status_info.get("firmware", "N/A")}
Protocol: {status_info.get("protocol", "N/A")}

✅ AXL + RISPort lookup successful."""

    except Exception as e:
        return f"""❌ CUCM phone lookup failed.

Phone Tried: {phone_name}
CUCM Host: {CUCM_HOST}

Error Type: {type(e).__name__}
Error:
{str(e)}"""