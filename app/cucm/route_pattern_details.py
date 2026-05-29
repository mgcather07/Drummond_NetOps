from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep import Settings
from zeep.transports import Transport
from zeep.helpers import serialize_object
import logging
logger = logging.getLogger(__name__)
import os
import requests

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def get_route_pattern_details(pattern: str, partition: str) -> dict:
    try:
        axl_url = f"https://{CUCM_HOST}:8443/axl/"

        session = requests.Session()
        session.verify = False
        session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

        transport = Transport(session=session, timeout=30)

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

        response = service.getRoutePattern(
            pattern=pattern,
            routePartitionName=partition
        )

        route_pattern = serialize_object(response["return"]["routePattern"])

        route_list = "N/A"
        gateway = "N/A"
        route_option = route_pattern.get("routeOption", "N/A")
        provide_outside_dialtone = route_pattern.get("provideOutsideDialtone", "N/A")
        block_enable = route_pattern.get("blockEnable", "N/A")
        network_location = route_pattern.get("networkLocation", "N/A")
        called_party_transform_mask = route_pattern.get("calledPartyTransformationMask", "N/A")
        discard_digits = route_pattern.get("discardDigits", "N/A")
        prefix_digits = route_pattern.get("prefixDigitsOut", "N/A")

        destination = route_pattern.get("destination", {})

        if destination.get("routeListName"):
            route_list = destination["routeListName"].get("_value_1", "N/A")

        if destination.get("gatewayName"):
            gateway = destination["gatewayName"].get("_value_1", "N/A")

        return {
            "found": True,
            "pattern": pattern,
            "partition": partition,
            "route_list": route_list,
            "gateway": gateway,
            "route_option": route_option,
            "provide_outside_dialtone": provide_outside_dialtone,
            "block_enable": block_enable,
            "network_location": network_location,
            "called_party_transform_mask": called_party_transform_mask,
            "discard_digits": discard_digits,
            "prefix_digits": prefix_digits,
        }

    except Exception as e:
        return {
            "found": False,
            "pattern": pattern,
            "partition": partition,
            "error": str(e),
        }


def format_route_pattern_details(details: dict) -> str:
    if not details.get("found"):
        return f"""Route Pattern Details:
Status: ❌ Not Found / Error
Pattern: {details.get("pattern", "N/A")}
Partition: {details.get("partition", "N/A")}
Error: {details.get("error", "N/A")}"""

    return f"""Call Flow Routing:
Outbound Gateway/Trunk: {details.get("gateway", "N/A")}
Network Location: {details.get("network_location", "N/A")}
Discard Digits: {details.get("discard_digits", "N/A")}
Prefix Digits Out: {details.get("prefix_digits", "N/A")}
Called Party Transform Mask: {details.get("called_party_transform_mask", "N/A")}"""