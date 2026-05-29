from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import logging
import os
import requests

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def get_css_partitions(css_name: str) -> set:
    """
    Pulls the partitions assigned to a CUCM Calling Search Space.
    """

    if not css_name:
        return set()

    axl_url = f"https://{CUCM_HOST}:8443/axl/"

    session = requests.Session()
    session.verify = False
    session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

    transport = Transport(session=session, timeout=30)

    client = Client(
        wsdl="schema/15.0/AXLAPI.wsdl",
        transport=transport
    )

    service = client.create_service(
        "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
        axl_url
    )

    response = service.getCss(name=css_name)
    css = serialize_object(response["return"]["css"])

    partitions = set()

    members = css.get("members")

    if not members:
        return partitions

    member_list = members.get("member")

    if not member_list:
        return partitions

    if not isinstance(member_list, list):
        member_list = [member_list]

    for member in member_list:
        partition_name = member.get("routePartitionName")

        if isinstance(partition_name, dict):
            partition_name = partition_name.get("_value_1")

        if partition_name:
            partitions.add(partition_name)

    return partitions