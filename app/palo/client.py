# app/palo/client.py
"""
Shared PAN-OS XML API client helpers.

All Palo Alto handlers import from here so auth/connection config
lives in one place.

Env vars required:
  PALO_HOST     — firewall management IP or FQDN
  PALO_API_KEY  — generated via:
                  curl -k -X POST "https://<host>/api/?type=keygen&user=...&password=..."
"""

import logging
import os

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

PALO_HOST = os.getenv("PALO_HOST")
PALO_API_KEY = os.getenv("PALO_API_KEY")


def _check_config() -> None:
    if not PALO_HOST or not PALO_API_KEY:
        raise RuntimeError(
            "PALO_HOST and PALO_API_KEY must be set in .env to use Palo Alto commands."
        )


def palo_op(cmd_xml: str, timeout: int = 15) -> requests.Response:
    """
    Run a PAN-OS operational command.

    :param cmd_xml: XML string, e.g. '<show><system><info/></system></show>'
    :returns:       requests.Response — caller parses .text as XML
    """
    _check_config()
    url = f"https://{PALO_HOST}/api/"
    params = {"type": "op", "cmd": cmd_xml, "key": PALO_API_KEY}
    logger.debug("PAN-OS op: %s", cmd_xml[:120])
    resp = requests.get(url, params=params, verify=False, timeout=timeout)
    resp.raise_for_status()
    return resp


def palo_config_get(xpath: str, timeout: int = 15) -> requests.Response:
    """
    Fetch a config subtree by XPath.

    :param xpath:   PAN-OS config XPath
    :returns:       requests.Response — caller parses .text as XML
    """
    _check_config()
    url = f"https://{PALO_HOST}/api/"
    params = {"type": "config", "action": "get", "xpath": xpath, "key": PALO_API_KEY}
    logger.debug("PAN-OS config get: %s", xpath[:120])
    resp = requests.get(url, params=params, verify=False, timeout=timeout)
    resp.raise_for_status()
    return resp
