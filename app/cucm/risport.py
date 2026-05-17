from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import os
import requests
from app.data.model_lookup import MODEL_LOOKUP

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()

def get_phone_status(phone_name: str) -> dict:
    """
    Uses CUCM RISPort API to get live phone registration/status info.
    """

    try:
        session = requests.Session()
        session.verify = False
        session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

        transport = Transport(session=session, timeout=15)

        wsdl = f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70?wsdl"

        client = Client(
            wsdl=wsdl,
            transport=transport
        )

        criteria = {
            "MaxReturnedDevices": 1000,
            "DeviceClass": "Phone",
            "Model": 255,
            "Status": "Any",
            "NodeName": "",
            "SelectBy": "Name",
            "SelectItems": {
                "item": [
                    {
                        "Item": phone_name
                    }
                ]
            },
            "Protocol": "Any",
            "DownloadStatus": "Any"
        }

        service = client.create_service(
            "{http://schemas.cisco.com/ast/soap}RisBinding",
            f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70"
        )

        response = service.selectCmDeviceExt(
            StateInfo="",
            CmSelectionCriteria=criteria
        )

        data = serialize_object(response)

        nodes = data.get("SelectCmDeviceResult", {}).get("CmNodes", {}).get("item", [])

        if not isinstance(nodes, list):
            nodes = [nodes]

        for node in nodes:
            node_name = node.get("Name", "N/A")
            devices = node.get("CmDevices", {}).get("item", [])

            if not isinstance(devices, list):
                devices = [devices]

            for device in devices:
                if device.get("Name", "").upper() == phone_name.upper():
                    ip_address = "N/A"

                    model_id = device.get("Model", "N/A")
                    model_name = MODEL_LOOKUP.get(
                        model_id,
                        f"Unknown Model ({model_id})"
                    )

                    ip_entries = device.get("IPAddress", {}).get("item", [])
                    if not isinstance(ip_entries, list):
                        ip_entries = [ip_entries]

                    if ip_entries:
                        ip_address = ip_entries[0].get("IP", "N/A")

                    return {
                        "found": True,
                        "status": device.get("Status", "Unknown"),
                        "ip_address": ip_address,
                        "active_node": node_name,
                        "model": model_name,
                        "firmware": device.get("ActiveLoadID", "N/A"),
                        "protocol": device.get("Protocol", "N/A"),
                    }

        return {
            "found": False,
            "status": "Not Found",
            "ip_address": "N/A",
            "active_node": "N/A",
            "model": "N/A",
            "firmware": "N/A",
            "protocol": "N/A",
        }

    except Exception as e:
        return {
            "found": False,
            "status": f"RISPort Error: {str(e)}",
            "ip_address": "N/A",
            "active_node": "N/A",
            "model": "N/A",
            "firmware": "N/A",
            "protocol": "N/A",
            "error": str(e),
        }