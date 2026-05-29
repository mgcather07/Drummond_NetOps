# app/vsphere/power.py
"""
TASK-026: VM power state operations (master-role only).

Supported actions: on, off, restart, force-off

All power ops require a confirmation reply (handled by command_router.py
via PENDING_ACTIONS). This module only executes once confirmed.
"""

import logging

from app.vsphere.client import get_si
from app.vsphere.vms import _find_vm

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"on", "off", "restart", "force-off"}


def power_op(vm_name: str, action: str) -> str:
    """Execute a power operation. Called after user confirms."""
    action = action.lower()
    if action not in VALID_ACTIONS:
        return (
            f"❌ Unknown action `{action}`.\n"
            f"Valid actions: {', '.join(sorted(VALID_ACTIONS))}"
        )

    si = None
    try:
        si = get_si()
        vm = _find_vm(si.RetrieveContent(), vm_name)

        if vm is None:
            return f"❌ VM not found: `{vm_name}`"

        if action == "on":
            vm.PowerOn()
            logger.info("Power ON sent to %s", vm_name)
        elif action == "off":
            vm.ShutdownGuest()  # graceful via VMware Tools
            logger.info("Graceful shutdown sent to %s", vm_name)
        elif action == "restart":
            vm.RebootGuest()  # graceful reboot via VMware Tools
            logger.info("Graceful restart sent to %s", vm_name)
        elif action == "force-off":
            vm.PowerOff()  # hard power cut
            logger.info("FORCE OFF sent to %s", vm_name)

        return f"✅ `{action}` command sent to **{vm_name}**."

    except Exception as e:
        # GuestOperationsFault = tools not running → suggest force-off
        msg = str(e)
        if "GuestOperations" in msg or "tools" in msg.lower():
            from app.utils.responses import error
            return error(
                "VMware Tools is not running",
                hint=f"Use `/vsphere power {vm_name} force-off` for a hard power cut.",
            )
        from app.utils.responses import error, translate_exception
        logger.exception("Power op %s failed for %s", action, vm_name)
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass
