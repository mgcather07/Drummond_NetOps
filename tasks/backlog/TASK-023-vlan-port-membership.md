---
id: TASK-023
category: spec
phase: phase-5
status: backlog
---

# TASK-023: VLAN info and port membership

## User story

As a **network engineer**, I want to query VLAN assignments and port membership from Webex so I can answer "what VLAN is port Gi0/12 in?" and "what ports are in VLAN 100?" without SSH-ing to the switch.

## Why this matters

VLAN misconfiguration is one of the most common causes of connectivity issues. Confirming VLAN membership is a routine step in almost every Layer 2 troubleshooting workflow. This command eliminates the SSH hop for the most common Layer 2 data points.

## Scope

**In scope:**
- `/net vlan <device>` — list all VLANs on a device with their names and active port count
- `/net vlan <device> <vlan-id>` — list all ports in a specific VLAN
- `/net port <device> <interface>` — show VLAN membership for a specific port (access VLAN, trunk allowed VLANs, mode)

**Out of scope:**
- Creating or deleting VLANs
- Spanning tree state (separate command if needed later)
- QinQ or private VLAN queries

## References

- Netmiko pattern: `app/network/show_version.py`
- Device resolver: `app/network/device_resolver.py` (TASK-020)
- Commands:
  - VLAN brief: `show vlan brief`
  - VLAN detail: `show vlan id {vlan_id}`
  - Port switchport: `show interfaces {interface} switchport`
- Env vars: `NETWORK_USERNAME`, `NETWORK_PASSWORD`

## Files expected to change

- `app/network/vlan.py` — new: VLAN and port query handlers
- `app/webex/command_router.py` — add `/net vlan` and `/net port` routing
- `app/security/auth.py` — both commands → `network.read`

## Execution order

1. Create `app/network/vlan.py`:
   ```python
   import os, re
   from netmiko import ConnectHandler
   from app.network.device_resolver import resolve_device

   NETWORK_USERNAME = os.getenv("NETWORK_USERNAME")
   NETWORK_PASSWORD = os.getenv("NETWORK_PASSWORD")

   def get_vlans(device_name: str, vlan_id: str = None) -> str: ...
   def get_port_vlan(device_name: str, interface: str) -> str: ...
   ```

2. `get_vlans(device_name, vlan_id)`:
   - If `vlan_id` is None: run `show vlan brief`, parse all VLANs
   - If `vlan_id` given: run `show vlan id {vlan_id}`, parse port membership
   - Validate `vlan_id` is numeric (1–4094) before sending
   - Return formatted result; "VLAN {id} not found" if not present

3. `get_port_vlan(device_name, interface)`:
   - Run `show interfaces {interface} switchport`
   - Parse: Administrative Mode (access/trunk/dynamic), Operational Mode, Access VLAN, Trunk Native VLAN, Trunk Allowed VLANs
   - Return compact summary

4. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/net vlan"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/net vlan <device> [vlan-id]`"
       else:
           device = parts[2]
           vlan_id = parts[3] if len(parts) > 3 else None
           from app.network.vlan import get_vlans
           response_text = get_vlans(device, vlan_id)
   elif command_lower.startswith("/net port"):
       parts = command.split()
       if len(parts) < 4:
           response_text = "Usage: `/net port <device> <interface>`"
       else:
           from app.network.vlan import get_port_vlan
           response_text = get_port_vlan(parts[2], parts[3])
   ```

5. Add permissions:
   ```python
   "/net vlan": "network.read",
   "/net port": "network.read",
   ```

## Sample output

```
📋 VLANs on ACC-BLDGA-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━
VLAN  Name              Ports
1     default           Gi0/23, Gi0/24
10    VOICE             Gi0/1-20
100   DATA              Gi0/1-20
200   MGMT              Gi0/25, Gi0/26

4 active VLANs.
```

```
📋 VLAN 100 on ACC-BLDGA-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:  DATA
Ports: Gi0/1, Gi0/2, Gi0/3, Gi0/4, Gi0/5, Gi0/6, Gi0/7, Gi0/8
       Gi0/9, Gi0/10, Gi0/11, Gi0/12, Gi0/13, Gi0/14, Gi0/15, Gi0/16
       Gi0/17, Gi0/18, Gi0/19, Gi0/20

20 ports in VLAN 100.
```

```
🔌 Port Info: ACC-BLDGA-1 Gi0/12
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode:          access
Access VLAN:   100 (DATA)
Voice VLAN:    10 (VOICE)
Operational:   access
Admin state:   enabled
```

## Acceptance criteria

- [ ] `/net vlan ACC-BLDGA-1` lists all VLANs with names and port counts
- [ ] `/net vlan ACC-BLDGA-1 100` lists all ports in VLAN 100
- [ ] `/net port ACC-BLDGA-1 Gi0/12` shows VLAN mode, access VLAN, and voice VLAN
- [ ] Invalid VLAN ID (non-numeric or out of range) returns validation error
- [ ] VLAN not found returns clean "VLAN {id} not found" message
- [ ] Both commands gated by `network.read`

## Manual verification

1. `/net vlan ACC-BLDGA-1` — compare to `show vlan brief` CLI output
2. `/net vlan ACC-BLDGA-1 100` — verify port list matches CLI
3. `/net port ACC-BLDGA-1 Gi0/12` — verify mode and VLAN match CLI
4. `/net vlan ACC-BLDGA-1 999` — confirm "VLAN 999 not found"

## Gotchas & learned lessons

- `show vlan brief` doesn't show ports in trunk mode — a port in trunk mode won't appear in VLAN member lists even though it carries the VLAN. Make a note in output if any trunks exist.
- `show interfaces switchport` output format varies between IOS and IOS-XE. Parse by field label, not line number.
- Voice VLAN is shown separately in switchport output as `Voice VLAN:` — include it for completeness (IP phones use it).
- Port lists in `show vlan id` can be very long on a 48-port switch. Wrap the port list at ~60 chars for readability.
- NX-OS `show vlan brief` format is different from IOS — if NX-OS devices are in the registry, write a separate parser or use `textfsm`.
