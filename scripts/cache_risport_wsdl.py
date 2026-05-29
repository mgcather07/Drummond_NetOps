"""Download and cache the RISPort70 WSDL from CUCM locally.

Run once per CUCM version upgrade:
    python scripts/cache_risport_wsdl.py

Saves to schema/15.0/RISService70.wsdl so risport.py and trunk_status.py
use the local file instead of fetching on every request.
"""

import os
import sys

import requests
import urllib3
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings()
load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

if not all([CUCM_HOST, CUCM_USERNAME, CUCM_PASSWORD]):
    print("❌ CUCM_HOST, CUCM_USERNAME, CUCM_PASSWORD must be set in .env")
    sys.exit(1)

url = f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70?wsdl"
dest = "schema/15.0/RISService70.wsdl"

print(f"Downloading RISPort WSDL from {CUCM_HOST}…")
resp = requests.get(url, auth=HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD), verify=False, timeout=15)
resp.raise_for_status()

os.makedirs(os.path.dirname(dest), exist_ok=True)
with open(dest, "wb") as f:
    f.write(resp.content)

print(f"✅ Saved to {dest} ({len(resp.content):,} bytes)")
