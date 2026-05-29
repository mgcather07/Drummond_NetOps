---
id: TASK-027
category: spec
phase: phase-6
status: backlog
---

# TASK-027: Host, cluster and datastore status

## User story

As a **systems administrator**, I want to check ESXi host health, cluster resource utilization, and datastore capacity from Webex so I can quickly assess infrastructure health during incidents or capacity planning reviews.

## Why this matters

"Is any host in a bad state?", "How full are my datastores?", and "Is vSphere HA active on the cluster?" are the first three questions during a vSphere incident. Surfacing these in Webex — without opening vSphere Client — cuts triage time significantly, especially for on-call responders who may be on a phone.

## Scope

**In scope:**
- `/vsphere hosts` — list all ESXi hosts with connection state, power state, and CPU/memory utilization
- `/vsphere cluster` — cluster summary: HA state, DRS mode, total CPU/RAM, VMs running
- `/vsphere datastores` — list all datastores with capacity, free space, and % used (flag > 80%)

**Out of scope:**
- Host configuration changes
- Datastore provisioning
- Per-host VM list (use `/vsphere list` for that)

## References

- Client: `app/vsphere/client.py` (TASK-025)
- pyVmomi objects: `vim.HostSystem`, `vim.ClusterComputeResource`, `vim.Datastore`
- Container view pattern: same as TASK-025 VM listing
- Env vars: `VCENTER_HOST`, `VCENTER_USERNAME`, `VCENTER_PASSWORD`

## Files expected to change

- `app/vsphere/infra.py` — new: host, cluster, and datastore query handlers
- `app/webex/command_router.py` — add three new `/vsphere` subcommands
- `app/security/auth.py` — all three commands → `vsphere.read`

## Execution order

1. Create `app/vsphere/infra.py`:
   ```python
   from pyVim.connect import Disconnect
   from pyVmomi import vim
   from app.vsphere.client import get_si

   def get_hosts() -> str: ...
   def get_cluster() -> str: ...
   def get_datastores() -> str: ...
   ```

2. `get_hosts()`:
   - Container view on `vim.HostSystem`
   - For each host: `name`, `summary.runtime.connectionState` (connected/disconnected/notResponding), `summary.runtime.powerState`, CPU usage (`summary.quickStats.overallCpuUsage`), CPU total (`summary.hardware.cpuMhz * summary.hardware.numCpuCores`), memory usage/total
   - Flag any host not in `connected` + `poweredOn` state with `❌`

3. `get_cluster()`:
   - Container view on `vim.ClusterComputeResource`
   - For each cluster: `name`, HA config (`configurationEx.dasConfig.enabled`), DRS config (`configurationEx.drsConfig.enabled`, `defaultVmBehavior`), `summary.numEffectiveHosts`, `summary.numHosts`, `summary.totalCpu`, `summary.totalMemory`, `summary.numVmotions`

4. `get_datastores()`:
   - Container view on `vim.Datastore`
   - For each datastore: `name`, `summary.capacity`, `summary.freeSpace`, `summary.accessible`
   - Compute % used = `(capacity - freeSpace) / capacity * 100`
   - Flag `⚠️` if > 80% full, `❌` if not accessible

5. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/vsphere hosts"):
       from app.vsphere.infra import get_hosts
       response_text = get_hosts()
   elif command_lower.startswith("/vsphere cluster"):
       from app.vsphere.infra import get_cluster
       response_text = get_cluster()
   elif command_lower.startswith("/vsphere datastores"):
       from app.vsphere.infra import get_datastores
       response_text = get_datastores()
   ```

6. Add permissions:
   ```python
   "/vsphere hosts": "vsphere.read",
   "/vsphere cluster": "vsphere.read",
   "/vsphere datastores": "vsphere.read",
   ```

## Sample output

```
🖥️  ESXi Hosts (3 hosts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Host                    State      CPU Used  Mem Used
esxi-host-01            connected  22%       61%
esxi-host-02            connected  18%       74%
esxi-host-03 ❌         notResponding  —        —
```

```
🏗️  Cluster: Production-Cluster
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HA:           ✅ Enabled
DRS:          ✅ Enabled (Fully Automated)
Hosts:        2 effective / 3 total
Total CPU:    96 GHz
Total Memory: 384 GB
vMotions:     4 (last 24h)
```

```
💾 Datastores (4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Datastore          Capacity  Free    Used
DS-SAN-VOL01       4.0 TB    1.2 TB  70%
DS-SAN-VOL02       4.0 TB    640 GB  84% ⚠️
DS-LOCAL-HOST01    500 GB    210 GB  58%
DS-BACKUP ❌       2.0 TB    —       (not accessible)
```

## Acceptance criteria

- [ ] `/vsphere hosts` lists all ESXi hosts with connection state and resource utilization
- [ ] Hosts not in `connected/poweredOn` state are flagged with `❌`
- [ ] `/vsphere cluster` shows HA/DRS state and aggregate resources
- [ ] `/vsphere datastores` lists all datastores with capacity and % used
- [ ] Datastores > 80% full are flagged with `⚠️`
- [ ] Inaccessible datastores are flagged with `❌`
- [ ] All three commands gated by `vsphere.read`

## Manual verification

1. `/vsphere hosts` — compare to vSphere Client host list
2. Disconnect a test host — confirm `❌` flag appears in Webex output
3. `/vsphere cluster` — verify HA/DRS state matches vSphere Client
4. `/vsphere datastores` — verify capacity numbers match vSphere Client

## Gotchas & learned lessons

- CPU utilization on a host is `quickStats.overallCpuUsage` (MHz) / (`hardware.cpuMhz * numCpuCores`). Both fields are on `summary`. No separate API call needed.
- Memory: `quickStats.overallMemoryUsage` is in MB. `hardware.memorySize` is in bytes. Convert consistently.
- Cluster objects in pyVmomi: `vim.ClusterComputeResource` is a subclass of `vim.ComputeResource`. A standalone host without a cluster is `vim.ComputeResource`. If there's no cluster configured, `get_cluster()` should return "No clusters configured" rather than an error.
- Datastore capacity in bytes — convert to human-readable (TB/GB) for display.
- Always call `Disconnect(si)` in a `finally` block — same session-limit concern as TASK-025.
- vSAN datastores show differently in the API — capacity may show as 0 until vSAN is fully initialized. Note this in output if detected.
