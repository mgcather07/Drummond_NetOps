# app/vsphere/client.py
"""
vCenter connection factory.

Requires pyVmomi (Python 3.10+). All vsphere handlers import get_si() from here.

Env vars required:
  VCENTER_HOST      — vCenter hostname or IP
  VCENTER_USERNAME  — vCenter username (e.g. administrator@vsphere.local)
  VCENTER_PASSWORD  — vCenter password
"""

import logging
import os
import ssl

logger = logging.getLogger(__name__)

VCENTER_HOST = os.getenv("VCENTER_HOST")
VCENTER_USERNAME = os.getenv("VCENTER_USERNAME")
VCENTER_PASSWORD = os.getenv("VCENTER_PASSWORD")

_PYVM_MISSING = (
    "pyVmomi is not installed (requires Python 3.10+).\n"
    "Upgrade to Python 3.10 and run `pip install pyVmomi`."
)


def _check_config() -> None:
    if not VCENTER_HOST or not VCENTER_USERNAME or not VCENTER_PASSWORD:
        raise RuntimeError(
            "VCENTER_HOST, VCENTER_USERNAME, and VCENTER_PASSWORD must be set in .env."
        )


def get_si():
    """
    Return an authenticated vCenter ServiceInstance.
    Caller MUST call Disconnect(si) in a finally block.

    Raises RuntimeError if pyVmomi is not installed or credentials are missing.
    """
    try:
        from pyVim.connect import SmartConnect
    except ImportError:
        raise RuntimeError(_PYVM_MISSING)

    _check_config()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    logger.debug("Connecting to vCenter %s as %s", VCENTER_HOST, VCENTER_USERNAME)
    si = SmartConnect(
        host=VCENTER_HOST,
        user=VCENTER_USERNAME,
        pwd=VCENTER_PASSWORD,
        sslContext=context,
    )
    return si
