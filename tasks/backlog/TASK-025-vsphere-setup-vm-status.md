---
id: TASK-025
category: spec
phase: phase-6
status: backlog
---

# TASK-025: vSphere setup + VM status and inventory

## User story

As a **systems administrator**, I want to look up a VM's current power state, resource allocation, and host placement from Webex so I can check on VMs during incidents without opening the vSphere Client.

## Why this matters

The vSphere Client is slow to load, requires VPN, and requires a full browser session. For quick operational queries ("is the CUCM VM running?", "what host is it on?"), a Webex command is far faster. This task wires up the pyVmomi connection and delivers the two most-requested VM data points: status and inventory.

## Scope

**In scope:**
- `app/vsphere/client.py` — pyVmomi connection factory (ServiceInstance + SmartConnect)
- `/vsphere vm <name>` — power state, guest OS, resource allocation (CPU/RAM), host, datastore, IP
- `/vsphere list` — list all VMs with power state (condensed, for quick inventory)

**Out of scope:**
- Power operations (TASK-026)
- Host/cluster/datastore health (TASK-027)
- Network info (TASK-028)
- Snapshots (TASK-029)

## References

- pyVmomi docs: `https://github.com/vmware/pyvmomi`
- pyVmomi community samples: `https://github.com/vmware/pyvmomi-community-samples`
- Key API objects: `SmartConnect`, `Disconnect`, `vim.VirtualMachine`, `content.searchIndex.FindByDnsName()`
- Env vars needed: `VCENTER_HOST`, `VCENTER_USERNAME`, `VCENTER_PASSWORD` (add to `.env` and TASK-005 validation)

## Files expected to change

- `app/vsphere/__init__.py` — new (empty)
- `app/vsphere/client.py` — new: vCenter connection factory
- `app/vsphere/vms.py` — new: VM status and list handlers
- `app/webex/command_router.py` — add `/vsphere vm` and `/vsphere list` routing
- `app/security/auth.py` — both commands → `vsphere.read`
- `app/config/settings.py` — add `VCENTER_HOST`, `VCENTER_USERNAME`, `VCENTER_PASSWORD`
- `requirements.txt` — add `pyVmomi`

## Execution order

1. Add `pyVmomi` to `requirements.txt`.

2. Add env vars to `app/config/settings.py`:
   ```python
   VCENTER_HOST = os.getenv("VCENTER_HOST")
   VCENTER_USERNAME = os.getenv("VCENTER_USERNAME")
   VCENTER_PASSWORD = os.getenv("VCENTER_PASSWORD")
   ```

3. Create `app/vsphere/client.py`:
   ```python
   import ssl, os
   from pyVim.connect import SmartConnect, Disconnect

   def get_si():
       """Return a vCenter ServiceInstance. Caller must call Disconnect(si) after use."""
       context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
       context.check_hostname = False
       context.verify_mode = ssl.CERT_NONE
       si = SmartConnect(
           host=os.getenv("VCENTER_HOST"),
           user=os.getenv("VCENTER_USERNAME"),
           pwd=os.getenv("VCENTER_PASSWORD"),
           sslContext=context,
       )
       return si
   ```

4. Create `app/vsphere/vms.py`:
   ```python
   from pyVim.connect import Disconnect
   from pyVmomi import vim
   from app.vsphere.client import get_si

   def get_vm_status(name: str) -> str: ...
   def list_vms() -> str: ...
   def _find_vm(content, name: str): ...
   ```

5. `_find_vm(content, name)`:
   - Use `content.searchIndex.FindByDnsName(vmSearch=True, dnsName=name)` first
   - If None, walk `content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)` and match by `vm.name` (case-insensitive)
   - Return `None` if not found

6. `get_vm_status(name)`:
   - Connect via `get_si()`
   - Find VM by name
   - Extract: `summary.runtime.powerState`, `summary.config.numCpu`, `summary.config.memorySizeMB`, `summary.config.guestFullName`, `runtime.host.name`, `summary.guest.ipAddress`, `config.datastoreUrl`
   - Disconnect
   - Format and return

7. `list_vms()`:
   - Get all VMs via container view
   - Return: name, power state, host — one line per VM
   - Sort by power state (powered-on first), then name

8. Add permissions and routing:
   ```python
   "/vsphere vm": "vsphere.read",
   "/vsphere list": "vsphere.read",
   ```

## Sample output

```
🖥️  VM Status: CUCM-PUB-01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Power state:  ✅ Powered On
Guest OS:     Cisco Unified Communications Manager 14.0
CPUs:         4 vCPU
Memory:       16,384 MB (16 GB)
IP address:   10.10.5.10
Host:         esxi-host-01.drummond.local
Datastore:    DS-SAN-VOL01
```

```
🖥️  VM Inventory (8 VMs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CUCM-PUB-01       esxi-host-01
✅ CUCM-SUB-01       esxi-host-01
✅ CUC-01            esxi-host-02
✅ UCCX-01           esxi-host-02
✅ SFTP-01           esxi-host-01
⛔ OLD-TEST-VM       esxi-host-02
⛔ BACKUP-WIN2019    esxi-host-01
⛔ DEV-CENTOS-01     esxi-host-02
```

## Acceptance criteria

- [ ] `/vsphere vm CUCM-PUB-01` returns power state, CPU, memory, IP, and host
- [ ] `/vsphere list` returns all VMs with power state and host
- [ ] Unknown VM name returns clean "VM not found" message
- [ ] `VCENTER_HOST` not set → startup validation error (via TASK-005)
- [ ] vCenter connection failure returns clean error (not a pyVmomi exception)
- [ ] Both commands gated by `vsphere.read`

## Manual verification

1. `/vsphere vm <known-VM-name>` — confirm data matches vSphere Client
2. `/vsphere list` — confirm all VMs appear with correct power state
3. `/vsphere vm BOGUS-VM` — confirm clean "not found" response
4. Bad `VCENTER_PASSWORD` → confirm clean auth error

## Gotchas & learned lessons

- pyVmomi's `SmartConnect()` is a blocking call — this is another async/blocking I/O issue (see TASK-009). Wrap in `run_in_executor` for the async handler.
- Self-signed vCenter certs are the norm on-prem. `ssl.CERT_NONE` is necessary — don't spend time trying to get cert trust working.
- Always call `Disconnect(si)` — vCenter has session limits (default 500). Leaking sessions will eventually lock the bot out.
- VM name search via `FindByDnsName` only works if the guest tools are running and reporting the hostname. Always fall back to name-based container search.
- `summary.guest.ipAddress` is populated by VMware Tools. If tools aren't running (powered off, tools not installed), it returns `None`.
- Add `VCENTER_HOST`, `VCENTER_USERNAME`, `VCENTER_PASSWORD` to TASK-005's required env var list.
