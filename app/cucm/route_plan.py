from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import logging
import os
import re
import requests

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def normalize_pattern(value: str) -> str:
    if not value:
        return ""

    return re.sub(r"\D", "", str(value))


def get_used_route_plan_patterns() -> set[str]:
    axl_url = f"https://{CUCM_HOST}:8443/axl/"

    session = requests.Session()
    session.verify = False
    session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

    transport = Transport(session=session, timeout=20)

    client = Client(
        wsdl="schema/15.0/AXLAPI.wsdl",
        transport=transport
    )

    service = client.create_service(
        "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
        axl_url
    )

    sql = """
    SELECT dnorpattern
    FROM numplan
    WHERE dnorpattern IS NOT NULL
    """

    response = service.executeSQLQuery(sql=sql)
    data = serialize_object(response)

    rows = data.get("return", {}).get("row", [])

    if not rows:
        return set()

    if not isinstance(rows, list):
        rows = [rows]

    used_patterns = set()

    for row in rows:
        if not isinstance(row, list):
            row = [row]

        for column in row:
            if hasattr(column, "tag") and column.tag == "dnorpattern":
                normalized = normalize_pattern(column.text)

                if normalized:
                    used_patterns.add(normalized)

    return used_patterns


def is_did_used(did: str, used_patterns: set[str]) -> bool:
    did = normalize_pattern(did)
    last_4 = did[-4:]

    return did in used_patterns or last_4 in used_patterns