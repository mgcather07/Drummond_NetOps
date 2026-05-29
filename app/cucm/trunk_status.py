from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import os
import requests

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def get_trunk_status(trunk_name: str) -> dict:
    try:
        session = requests.Session()
        session.verify = False
        session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

        transport = Transport(session=session, timeout=20)

        # Prefer locally cached WSDL; fall back to live fetch
        _local_wsdl = "schema/15.0/RISService70.wsdl"
        wsdl = (
            _local_wsdl
            if os.path.exists(_local_wsdl)
            else f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70?wsdl"
        )

        client = Client(
            wsdl=wsdl,
            transport=transport
        )

        service = client.create_service(
            "{http://schemas.cisco.com/ast/soap}RisBinding",
            f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70"
        )

        criteria = {
            "MaxReturnedDevices": 1000,
            "DeviceClass": "Any",
            "Model": 255,
            "Status": "Any",
            "NodeName": "",
            "SelectBy": "Name",
            "SelectItems": {
                "item": [
                    {
                        "Item": trunk_name
                    }
                ]
            },
            "Protocol": "Any",
            "DownloadStatus": "Any"
        }

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
                if device.get("Name", "").upper() == trunk_name.upper():
                    return {
                        "found": True,
                        "status": device.get("Status", "Unknown"),
                        "active_node": node_name,
                        "model": device.get("Model", "N/A"),
                        "protocol": device.get("Protocol", "N/A"),
                        "description": device.get("Description", "N/A"),
                    }

        return {
            "found": False,
            "status": "Not Found",
            "active_node": "N/A",
            "model": "N/A",
            "protocol": "N/A",
            "description": "N/A",
        }

    except Exception as e:
        return {
            "found": False,
            "status": f"RISPort Error: {str(e)}",
            "active_node": "N/A",
            "model": "N/A",
            "protocol": "N/A",
            "description": "N/A",
        }