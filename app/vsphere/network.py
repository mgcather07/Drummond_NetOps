# app/vsphere/network.py
"""
TASK-028: VM vNIC, port group, VLAN, and guest IP info.

Commands:
  /vsphere net <vm>           — list all vNICs with MAC, PG, VLAN, IPs
  /vsphere portgroup <name>   — VMs connected to a port group
"""

import logging

from app.vsphere.client import get_si
from app.vsphere.vms import _find_vm

logger = logging.getLogger(__name__)


def _get_vlan_id(pg) -> str:
    """Extract VLAN ID from a port group config (standard or distributed)."""
    try:
        from pyVmomi import vim
        if isinstance(pg, vim.dvs.DistributedVirtualPortgroup):
            vlan_cfg = pg.config.defaultPortConfig.vlan
            vlan_type = type(vlan_cfg).__name__
            if "VlanId" in vlan_type:
                return str(vlan_cfg.vlanId)
            if "Trunk" in vlan_type:
                ranges = vlan_cfg.vlanId
                return ",".join(f"{r.start}-{r.end}" for r in ranges[:3])
            return "N/A (PVLAN)"
        elif isinstance(pg, vim.Network):
            return str(getattr(pg.config, "vlanId", "N/A"))
    except Exception:
        pass
    return "N/A"


def get_vm_network(vm_name: str) -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        vm = _find_vm(content, vm_name)

        if vm is None:
            return f"❌ VM not found: `{vm_name}`"

        from pyVmomi import vim

        # Build MAC → guest IPs map from VMware Tools guest data
        mac_to_ips: dict = {}
        if vm.guest and vm.guest.net:
            for nic_info in vm.guest.net:
                mac = (nic_info.macAddress or "").lower()
                ips = [ip for ip in (nic_info.ipAddress or []) if ip]
                if mac:
                    mac_to_ips[mac] = ips

        nics = [
            dev for dev in (vm.config.hardware.device or [])
            if isinstance(dev, vim.vm.device.VirtualEthernetCard)
        ]

        if not nics:
            return f"🔌 VM Network: {vm_name}\n━━━━━━━━━━━━━━━━━━━━━━━━\nNo network adapters found."

        lines = [f"🔌 VM Network: {vm_name}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        for nic in nics:
            label = nic.deviceInfo.label if nic.deviceInfo else "NIC"
            mac = (nic.macAddress or "N/A").lower()
            adapter_type = type(nic).__name__.replace("Virtual", "")

            # Port group name and type
            pg_name = "N/A"
            pg_type = "standard"
            vlan_id = "N/A"
            backing = nic.backing
            if hasattr(backing, "deviceName"):
                pg_name = backing.deviceName
            elif hasattr(backing, "port") and hasattr(backing.port, "portgroupKey"):
                # Distributed vSwitch — look up the PG name
                pg_key = backing.port.portgroupKey
                try:
                    all_pgs = content.viewManager.CreateContainerView(
                        content.rootFolder, [vim.dvs.DistributedVirtualPortgroup], True
                    )
                    for pg in all_pgs.view:
                        if pg.key == pg_key:
                            pg_name = pg.name
                            pg_type = "dvSwitch"
                            vlan_id = _get_vlan_id(pg)
                            break
                    all_pgs.Destroy()
                except Exception:
                    pg_name = f"(dvPG key: {pg_key})"

            guest_ips = mac_to_ips.get(mac, [])
            ip_str = ", ".join(guest_ips) if guest_ips else "(tools not running)"

            lines += [
                f"\n**{label}**",
                f"  Adapter:    {adapter_type}",
                f"  MAC:        {mac}",
                f"  Port group: {pg_name} ({pg_type})",
                f"  VLAN:       {vlan_id}",
                f"  Guest IPs:  {ip_str}",
            ]

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("VM network info failed for %s", vm_name)
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass


def get_portgroup_vms(pg_name: str) -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        from pyVmomi import vim

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Network], True
        )
        pgs = list(container.view)
        container.Destroy()

        pg = None
        for p in pgs:
            if p.name.lower() == pg_name.lower():
                pg = p
                break

        if pg is None:
            return (
                f"❌ Port group `{pg_name}` not found.\n\n"
                "Use `/vsphere net <vm>` to see a VM's port groups."
            )

        vms = list(pg.vm) if pg.vm else []
        pg_type = "Distributed" if isinstance(pg, vim.dvs.DistributedVirtualPortgroup) else "Standard"
        vlan_id = _get_vlan_id(pg)

        lines = [
            f"🔌 Port Group: {pg.name}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"VLAN:  {vlan_id}",
            f"Type:  {pg_type}",
            f"VMs:   {len(vms)} connected",
            "",
        ]
        for vm in sorted(vms, key=lambda v: v.name.lower()):
            state = vm.summary.runtime.powerState
            icon = "✅" if state == "poweredOn" else "⛔"
            lines.append(f"{icon} {vm.name}")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Port group VMs query failed for %s", pg_name)
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass
