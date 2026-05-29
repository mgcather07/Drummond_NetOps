---
id: TASK-029
category: spec
phase: phase-6
status: backlog
---

# TASK-029: Snapshot inventory and age report

## User story

As a **systems administrator**, I want to list all VM snapshots in the environment with their age so I can identify stale snapshots that are consuming datastore space, and confirm when a specific VM's snapshot was taken — all from Webex.

## Why this matters

Forgotten snapshots are one of the most common causes of unexpected datastore growth in vSphere environments. A snapshot taken "temporarily" before a change and never deleted can quietly consume hundreds of GBs. A Webex command that surfaces all snapshots older than a configurable threshold (default: 7 days) gives the team a regular hygiene check without opening the vSphere Client.

## Scope

**In scope:**
- `/vsphere snapshots` — list all VMs that have snapshots, with snapshot name, age, and size
- `/vsphere snapshots <vm-name>` — snapshot tree for a specific VM
- Flag snapshots older than 7 days with `⚠️` and older than 30 days with `❌`

**Out of scope:**
- Creating snapshots (write operation — not needed for ops queries)
- Deleting snapshots (destructive — keep out of chat commands)
- Snapshot quiesce or memory state details

## References

- Client: `app/vsphere/client.py` (TASK-025)
- VM finder: `_find_vm()` in `app/vsphere/vms.py` (TASK-025)
- pyVmomi snapshot tree: `vm.snapshot.rootSnapshotList` → recursive `childSnapshotList`
- Snapshot object fields: `snap.name`, `snap.createTime`, `snap.description`, `snap.id`
- Note: snapshot *size on disk* is not directly available via the API — report age only
- Env vars: `VCENTER_HOST`, `VCENTER_USERNAME`, `VCENTER_PASSWORD`

## Files expected to change

- `app/vsphere/snapshots.py` — new: snapshot inventory handler
- `app/webex/command_router.py` — add `/vsphere snapshots` routing
- `app/security/auth.py` — `vsphere.read` permission

## Execution order

1. Create `app/vsphere/snapshots.py`:
   ```python
   from datetime import datetime, timezone
   from pyVim.connect import Disconnect
   from pyVmomi import vim
   from app.vsphere.client import get_si
   from app.vsphere.vms import _find_vm

   WARN_DAYS = 7
   CRITICAL_DAYS = 30

   def _flatten_snapshots(snap_list, depth=0) -> list[dict]:
       """Recursively flatten the snapshot tree into a list of dicts."""
       result = []
       for snap in snap_list:
           age_days = (datetime.now(timezone.utc) - snap.createTime).days
           result.append({
               "name": snap.name,
               "description": snap.description,
               "created": snap.createTime,
               "age_days": age_days,
               "depth": depth,
           })
           result.extend(_flatten_snapshots(snap.childSnapshotList, depth + 1))
       return result

   def get_all_snapshots() -> str: ...
   def get_vm_snapshots(vm_name: str) -> str: ...
   ```

2. `get_all_snapshots()`:
   - Container view on `vim.VirtualMachine`
   - For each VM, check if `vm.snapshot` is not None
   - Flatten snapshot tree
   - Sort by age (oldest first)
   - Output: VM name + snapshot count as header, then each snapshot with age flag
   - If total across all VMs is 0 → "✅ No snapshots found in the environment."

3. `get_vm_snapshots(vm_name)`:
   - Find VM by name
   - If `vm.snapshot` is None → return "No snapshots on `{vm_name}`."
   - Flatten snapshot tree with indentation for child snapshots
   - Show tree structure (parent → child)

4. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/vsphere snapshots"):
       parts = command.split()
       if len(parts) >= 3:
           vm_name = parts[2]
           from app.vsphere.snapshots import get_vm_snapshots
           response_text = get_vm_snapshots(vm_name)
       else:
           from app.vsphere.snapshots import get_all_snapshots
           response_text = get_all_snapshots()
   ```

5. Add `"/vsphere snapshots": "vsphere.read"` to `COMMAND_PERMISSIONS`.

## Age flagging logic

```python
def _age_flag(age_days: int) -> str:
    if age_days >= CRITICAL_DAYS:
        return "❌"
    elif age_days >= WARN_DAYS:
        return "⚠️"
    return "  "
```

## Sample output

```
📸 Snapshot Inventory (5 snapshots across 3 VMs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OLD-TEST-VM (2 snapshots)
  ❌ Pre-upgrade-snapshot   taken 2026-03-01  (88 days ago)
  ❌ Post-upgrade-check     taken 2026-03-02  (87 days ago)

CUCM-PUB-01 (1 snapshot)
  ⚠️ before-patch-may-20   taken 2026-05-20  (8 days ago)

DEV-CENTOS-01 (2 snapshots)
     dev-baseline          taken 2026-05-27  (1 day ago)
     after-config-change   taken 2026-05-28  (today)

Legend: ❌ > 30 days  ⚠️ > 7 days
```

```
📸 Snapshots: CUCM-PUB-01
━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ before-patch-may-20  (2026-05-20, 8 days ago)
    "Snapshot before May patch window"
    └─ (no children)
```

## Acceptance criteria

- [ ] `/vsphere snapshots` lists all VMs with snapshots, sorted oldest-first
- [ ] Snapshots > 7 days flagged `⚠️`, > 30 days flagged `❌`
- [ ] `/vsphere snapshots CUCM-PUB-01` shows snapshot tree for that VM
- [ ] No snapshots in environment → "✅ No snapshots found"
- [ ] VM with no snapshots → "No snapshots on `{vm_name}`"
- [ ] Child snapshots (snapshot chains) are shown indented under parent
- [ ] Command gated by `vsphere.read`

## Manual verification

1. `/vsphere snapshots` — compare to vSphere Client snapshot manager
2. Create a test snapshot, run `/vsphere snapshots <vm>` — confirm it appears
3. `/vsphere snapshots NO-SUCH-VM` — confirm clean "VM not found"
4. Environment with no snapshots — confirm clean "no snapshots" message

## Gotchas & learned lessons

- `vm.snapshot` is `None` when a VM has no snapshots — always check before accessing `rootSnapshotList`.
- `snap.createTime` is timezone-aware (UTC). Use `datetime.now(timezone.utc)` for comparison — don't use `datetime.utcnow()` (naive).
- Snapshot chains (parent → child) are common after multiple incremental snapshots. The `childSnapshotList` is recursive. The `_flatten_snapshots()` recursive helper handles arbitrarily deep chains.
- Snapshot disk size is NOT reliably available via the API — the `.vmsn` and delta `.vmdk` files are visible on the datastore but not directly reported per-snapshot in pyVmomi. Report age only; for size, the operator checks the datastore browser.
- Large environments (100+ VMs, many with snapshots) can produce a lot of output. Truncate to the 20 most-critical snapshots and report a count if > 20.
- `/vsphere snapshots` is a good candidate for a scheduled daily alert (future work) — but for now, on-demand is sufficient.
