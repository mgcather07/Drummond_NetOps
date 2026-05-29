---
id: TASK-028
category: spec
phase: phase-6
status: backlog
---

# TASK-028: VM network info (vNIC, port group, VLAN)

## User story

As a **systems administrator or network engineer**, I want to see which virtual network interfaces a VM has, what port group and VLAN each one is on, and what IP addresses the guest is using — from Webex — so I can diagnose VM connectivity issues without switching between the vSphere Client and the network team's tools.

## Why this matters

VM network misconfiguration ("why can't this VM talk to the SQL server?") often requires cross-referencing the vSphere port group assignment, the VLAN tag, and the guest IP — three pieces of data that live in three different views in the GUI. One Webex command that surfaces all three eliminates the context switching and speeds up diagnosis.

## Scope

**In scope:**
- `/vsphere net <vm-name>` — list all vNICs for a VM: adapter type, MAC, port group, VLAN, guest IP (if available via VMware Tools)
- `/vsphere portgroup <name>` — list all VMs connected to a named port group

**Out of scope:**
- Modifying network adapter config
- dvSwitch uplink/LAG detail
- NSX-T overlay network detail

## References

- Client: `app/vsphere/client.py` (TASK-025)
- VM finder: `_find_vm()` in `app/vsphere/vms.py` (TASK-025)
- pyVmomi objects: `vim.vm.device.VirtualEthernetCard`, `vim.dvs.DistributedVirtualPortgroup`, `vim.Network`
- Guest NIC info: `vm.guest.net` (list of `GuestNicInfo`)
- Env vars: `VCENTER_HOST`, `VCENTER_USERNAME`, `VCENTER_PASSWORD`

## Files expected to change

- `app/vsphere/network.py` — new: VM NIC and port group handlers
- `app/webex/command_router.py` — add `/vsphere net` and `/vsphere portgroup` routing
- `app/security/auth.py` — both commands → `vsphere.read`

## Execution order

1. Create `app/vsphere/network.py`:
   ```python
   from pyVim.connect import Disconnect
   from pyVmomi import vim
   from app.vsphere.client import get_si
   from app.vsphere.vms import _find_vm

   def get_vm_network(vm_name: str) -> str: ...
   def get_portgroup_vms(pg_name: str) -> str: ...
   ```

2. `get_vm_network(vm_name)`:
   - Find VM by name
   - Walk `vm.config.hardware.device`, filter for `isinstance(dev, vim.vm.device.VirtualEthernetCard)`
   - For each NIC:
     - `dev.deviceInfo.label` (e.g. "Network adapter 1")
     - `dev.macAddress`
     - `dev.backing`: if `VirtualEthernetCard.NetworkBackingInfo` → `backing.deviceName` (port group name); if `VirtualEthernetCard.DistributedVirtualPortBackingInfo` → look up dvPortgroup name via `backing.port.portgroupKey`
     - VLAN ID: for standard vSwitch, look up port group config; for dvSwitch, `dvpg.config.defaultPortConfig.vlan.vlanId`
   - Cross-reference `vm.guest.net` to add IPs by MAC match
   - Format per NIC

3. `get_portgroup_vms(pg_name)`:
   - Container view on `vim.Network` (covers both standard and distributed port groups)
   - Find port group by name (case-insensitive)
   - `pg.vm` → list of `vim.VirtualMachine` objects connected to it
   - Return: port group name, VLAN, count, list of VM names + power state

4. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/vsphere net"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/vsphere net <vm-name>`"
       else:
           from app.vsphere.network import get_vm_network
           response_text = get_vm_network(parts[2])
   elif command_lower.startswith("/vsphere portgroup"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/vsphere portgroup <portgroup-name>`"
       else:
           pg_name = " ".join(parts[2:])  # port group names can have spaces
           from app.vsphere.network import get_portgroup_vms
           response_text = get_portgroup_vms(pg_name)
   ```

5. Add permissions:
   ```python
   "/vsphere net": "vsphere.read",
   "/vsphere portgroup": "vsphere.read",
   ```

## Sample output

```
🔌 VM Network: CUCM-PUB-01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIC 1 (Network adapter 1)
  Adapter:    vmxnet3
  MAC:        00:50:56:ab:12:34
  Port group: VOICE-VLAN-10 (dvSwitch)
  VLAN:       10
  Guest IPs:  10.10.5.10, fe80::250:56ff:feab:1234

NIC 2 (Network adapter 2)
  Adapter:    vmxnet3
  MAC:        00:50:56:ab:56:78
  Port group: MGMT-VLAN-200 (dvSwitch)
  VLAN:       200
  Guest IPs:  10.10.200.10
```

```
🔌 Port Group: VOICE-VLAN-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VLAN:  10
Type:  Distributed (dvSwitch-Production)
VMs:   4 connected

✅ CUCM-PUB-01
✅ CUCM-SUB-01
✅ CUC-01
⛔ CUCM-PUB-01-OLD
```

## Acceptance criteria

- [ ] `/vsphere net CUCM-PUB-01` lists all vNICs with MAC, port group, VLAN, and guest IPs
- [ ] Both standard vSwitch and distributed vSwitch port group names resolve correctly
- [ ] VLAN IDs are shown for all NICs (not just dvSwitch)
- [ ] Guest IPs shown when VMware Tools is running; "(tools not running)" when not
- [ ] `/vsphere portgroup VOICE-VLAN-10` lists all connected VMs with power state
- [ ] Port group names with spaces work (join remaining args)
- [ ] Both commands gated by `vsphere.read`

## Manual verification

1. `/vsphere net <known-VM>` — compare NIC/VLAN info to vSphere Client
2. `/vsphere portgroup <known-pg>` — verify VM list matches vSphere Client
3. On a VM with tools stopped — confirm "(tools not running)" appears for IPs
4. `/vsphere portgroup "unknown portgroup"` — confirm clean "not found" message

## Gotchas & learned lessons

- dvPortgroup VLAN config is in `pg.config.defaultPortConfig.vlan`. The type varies: `VmwareDistributedVirtualSwitchVlanIdSpec` (single VLAN), `VmwareDistributedVirtualSwitchTrunkVlanSpec` (VLAN range), or `VmwareDistributedVirtualSwitchPvlanSpec` (PVLAN). Handle all three.
- Standard port group VLAN is in `pg.config.vlanId` (simple integer). Much simpler.
- `vm.guest.net` returns a list of `GuestNicInfo`; each has `macAddress` and `ipAddresses`. Match by MAC to correlate with the hardware device list.
- Port group name lookup: `vim.Network` covers both standard and distributed. If you want the dvSwitch name, that's on `vim.dvs.DistributedVirtualPortgroup` — use `isinstance()` to distinguish.
- Port group names sometimes have spaces (e.g. "VM Network", "VLAN 100 - Data"). Use `" ".join(parts[2:])` to reconstruct the full name.
