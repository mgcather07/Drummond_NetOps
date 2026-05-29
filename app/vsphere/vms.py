# app/vsphere/vms.py
"""
TASK-025: VM status and inventory.

Commands:
  /vsphere vm <name>  — power state, resources, IP, host
  /vsphere list       — all VMs with power state
"""

import logging

from app.vsphere.client import get_si

logger = logging.getLogger(__name__)


def _find_vm(content, name: str):
    """Find a VM by name (case-insensitive). Returns vim.VirtualMachine or None."""
    try:
        from pyVmomi import vim
    except ImportError:
        return None

    # Try DNS name index first (only works if VMware Tools is running)
    vm = content.searchIndex.FindByDnsName(vmSearch=True, dnsName=name)
    if vm:
        return vm

    # Full container walk
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    for vm in container.view:
        if vm.name.lower() == name.lower():
            container.Destroy()
            return vm
    container.Destroy()
    return None


def get_vm_status(name: str) -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        vm = _find_vm(content, name)

        if vm is None:
            return f"❌ VM not found: `{name}`\n\nUse `/vsphere list` to see available VMs."

        summary = vm.summary
        runtime = summary.runtime
        config = summary.config
        guest = summary.guest

        power_state = runtime.powerState
        power_icon = "✅" if power_state == "poweredOn" else "⛔"

        ip = (guest.ipAddress or "(tools not running)") if guest else "(tools not running)"
        hostname_display = (guest.hostName or name) if guest else name
        host_name = runtime.host.name if runtime.host else "N/A"
        ds_url = config.vmPathName if config else "N/A"

        lines = [
            f"🖥️  VM Status: {name}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Power state:  {power_icon} {power_state}",
            f"Guest OS:     {config.guestFullName if config else 'N/A'}",
            f"CPUs:         {config.numCpu if config else 'N/A'} vCPU",
            f"Memory:       {config.memorySizeMB:,} MB" if (config and config.memorySizeMB) else "Memory:       N/A",
            f"IP address:   {ip}",
            f"Host:         {host_name}",
            f"Datastore:    {ds_url}",
        ]
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("VM status failed for %s", name)
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass


def list_vms() -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        from pyVmomi import vim

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        vms = list(container.view)
        container.Destroy()

        if not vms:
            return "🖥️  VM Inventory\n━━━━━━━━━━━━━━━━━━━━━━━━\nNo VMs found."

        # Sort: powered-on first, then by name
        vms.sort(key=lambda v: (
            0 if v.summary.runtime.powerState == "poweredOn" else 1,
            v.name.lower()
        ))

        lines = [f"🖥️  VM Inventory ({len(vms)} VMs)", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        MAX = 50
        for vm in vms[:MAX]:
            state = vm.summary.runtime.powerState
            icon = "✅" if state == "poweredOn" else "⛔"
            host = vm.summary.runtime.host.name if vm.summary.runtime.host else "N/A"
            # Trim host to just hostname portion
            host_short = host.split(".")[0] if "." in host else host
            lines.append(f"{icon} {vm.name:<30} {host_short}")

        if len(vms) > MAX:
            lines.append(f"\n… {len(vms) - MAX} more VMs not shown.")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("VM list failed")
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass
