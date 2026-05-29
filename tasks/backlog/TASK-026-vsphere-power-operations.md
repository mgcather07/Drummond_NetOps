---
id: TASK-026
category: spec
phase: phase-6
status: backlog
---

# TASK-026: VM power state operations

## User story

As a **systems administrator with master-role access**, I want to power on, power off, and restart VMs from Webex so I can perform controlled recovery operations during incidents without opening the vSphere Client or remoting into a management host.

## Why this matters

Scheduled restarts and incident recovery often happen at odd hours when access to the vSphere Client is slow or inconvenient. A controlled, logged Webex command for power operations — gated behind master-role RBAC and a confirmation step — gives the right people a faster, auditable path without opening broad access.

## Scope

**In scope:**
- `/vsphere power <vm-name> on` — power on a VM
- `/vsphere power <vm-name> off` — graceful shutdown (VMware Tools guest shutdown)
- `/vsphere power <vm-name> restart` — graceful guest restart (VMware Tools)
- `/vsphere power <vm-name> force-off` — hard power off (no guest shutdown)
- Confirmation step before any destructive action (using `PENDING_ACTIONS`)

**Out of scope:**
- Suspend/resume
- Snapshot before power-off (separate op — do manually)
- Migrate VM between hosts
- Bulk power operations

## References

- VM status + client: `app/vsphere/client.py`, `app/vsphere/vms.py` (TASK-025)
- Multi-step confirmation pattern: `app/state/pending_actions.py`, `app/cucm/phones_eol.py`
- pyVmomi power APIs: `vm.PowerOn()`, `vm.ShutdownGuest()`, `vm.RebootGuest()`, `vm.PowerOff()`
- RBAC: `app/security/auth.py` — this is a `vsphere.write` permission (master-only)

## Files expected to change

- `app/vsphere/power.py` — new: power operation handlers
- `app/webex/command_router.py` — add `/vsphere power` routing + confirmation handling
- `app/security/auth.py` — add `vsphere.write` permission (master role only)

## Execution order

1. Add `vsphere.write` to `ROLE_PERMISSIONS` in `auth.py`:
   ```python
   ROLE_PERMISSIONS = {
       "master": ["*"],  # already covers it, but add explicit vsphere.write for clarity
       "admin": ["cucm.read", "cucm.health", "network.read", "vsphere.read"],
       "user": ["cucm.read"],
   }
   ```

2. Add to `COMMAND_PERMISSIONS`:
   ```python
   "/vsphere power": "vsphere.write",
   ```

3. Create `app/vsphere/power.py`:
   ```python
   from pyVim.connect import Disconnect
   from app.vsphere.client import get_si
   from app.vsphere.vms import _find_vm

   VALID_ACTIONS = {"on", "off", "restart", "force-off"}

   def power_op(vm_name: str, action: str) -> str:
       """Execute a power operation on a named VM. Returns result message."""
       if action not in VALID_ACTIONS:
           return f"❌ Unknown action `{action}`. Valid: {', '.join(sorted(VALID_ACTIONS))}"
       si = get_si()
       try:
           vm = _find_vm(si.RetrieveContent(), vm_name)
           if vm is None:
               return f"❌ VM not found: `{vm_name}`"
           if action == "on":
               vm.PowerOn()
           elif action == "off":
               vm.ShutdownGuest()   # graceful via tools
           elif action == "restart":
               vm.RebootGuest()     # graceful via tools
           elif action == "force-off":
               vm.PowerOff()        # hard stop
           return f"✅ `{action}` sent to **{vm_name}**."
       finally:
           Disconnect(si)
   ```

4. Wire multi-step confirmation in `command_router.py`:
   ```python
   elif command_lower.startswith("/vsphere power"):
       parts = command.split()
       if len(parts) < 4:
           response_text = "Usage: `/vsphere power <vm-name> <on|off|restart|force-off>`"
       else:
           vm_name, action = parts[2], parts[3].lower()
           # Store pending action, ask for confirmation
           PENDING_ACTIONS[sender_email] = {
               "type": "vsphere_power",
               "vm_name": vm_name,
               "action": action,
               "created_at": time.time(),
           }
           verb = {"on": "power on", "off": "shut down", "restart": "restart", "force-off": "FORCE OFF"}.get(action, action)
           warn = " ⚠️ **This is a hard power cut.**" if action == "force-off" else ""
           response_text = (
               f"⚡ Confirm: {verb} VM **{vm_name}**?{warn}\n\n"
               f"Reply `yes` to confirm or `no` to cancel."
           )
   ```

5. Handle confirmation reply in the pending-action check at the top of `command_router.py`:
   ```python
   if sender_email in PENDING_ACTIONS:
       pending = PENDING_ACTIONS[sender_email]
       if pending.get("type") == "vsphere_power":
           PENDING_ACTIONS.pop(sender_email)
           if command_lower.strip() == "yes":
               from app.vsphere.power import power_op
               response_text = power_op(pending["vm_name"], pending["action"])
           else:
               response_text = "Cancelled."
           # send and return early
   ```

## Sample flow

```
User: /vsphere power CUCM-PUB-01 restart
Bot:  ⚡ Confirm: restart VM CUCM-PUB-01?
      Reply `yes` to confirm or `no` to cancel.

User: yes
Bot:  ✅ `restart` sent to CUCM-PUB-01.
```

```
User: /vsphere power OLD-TEST-VM force-off
Bot:  ⚡ Confirm: FORCE OFF VM OLD-TEST-VM? ⚠️ This is a hard power cut.
      Reply `yes` to confirm or `no` to cancel.

User: no
Bot:  Cancelled.
```

## Acceptance criteria

- [ ] `/vsphere power <vm> restart` triggers a confirmation prompt
- [ ] Replying `yes` executes the operation and returns a success message
- [ ] Replying `no` (or anything else) cancels and returns "Cancelled."
- [ ] `force-off` shows an extra warning in the confirmation prompt
- [ ] All power operations gated by `vsphere.write` (master role only)
- [ ] `admin` or `user` role attempting `/vsphere power` gets "permission denied"
- [ ] Unknown VM name returns clean error before confirmation prompt
- [ ] Invalid action (`/vsphere power MYVM nuke`) returns valid action list

## Manual verification

1. `/vsphere power <powered-off-vm> on` → confirm → verify VM powers on in vSphere Client
2. `/vsphere power <running-vm> restart` → confirm → verify guest restarts cleanly
3. As `admin` role: `/vsphere power <vm> on` → confirm permission denied
4. `/vsphere power BOGUS-VM on` → confirm "VM not found" without prompting

## Gotchas & learned lessons

- `ShutdownGuest()` and `RebootGuest()` require VMware Tools to be running. If tools are stopped or not installed, the call raises a fault. Catch it and suggest `force-off` if graceful shutdown fails.
- `PowerOn()` and `PowerOff()` return a `Task` object — they're async at the vCenter layer. The Webex response says "sent to VM", not "complete". For power-on, a follow-up status check is the right UX.
- The TTL on `PENDING_ACTIONS` (TASK-007) is especially important here — a stale "yes" response from 10 minutes ago should not trigger a power-off. Ensure the 5-minute TTL is enforced before this task ships.
- Only implement `vsphere.write` as master-role — this is a destructive operation and should not be handed to admin-role users.
- Log every power operation to the application log with `sender_email`, `vm_name`, `action`, and timestamp — this creates an audit trail without a separate audit table.
