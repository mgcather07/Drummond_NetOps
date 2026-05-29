---
id: TASK-017
category: spec
phase: phase-4
status: backlog
---

# TASK-017: Palo Alto HA status & system health

## User story

As a **network engineer**, I want to query the Palo Alto firewall's HA state and system health from Webex so I can quickly confirm whether the firewall pair is in sync and what its resource utilization looks like without opening a browser or SSH session.

## Why this matters

The firewall HA state is one of the first things checked during an incident. Today that means logging into Panorama or SSH-ing to the firewall CLI. This command puts that data in Webex in under two seconds. TASK-010 adds the first Palo Alto command (`/palo policy` and `/palo nat`); this task adds the operational health layer on top of the same PAN-OS XML API client.

## Scope

**In scope:**
- `/palo health` — system resource summary (CPU, memory, session count, uptime)
- `/palo ha` — HA pair state (active/passive, sync status, peer reachable)
- Shared PAN-OS API client extracted into `app/palo/client.py` (so all palo commands reuse one authenticated session)

**Out of scope:**
- Panorama multi-device queries
- Historical resource trending
- Pushing config changes

## References

- PAN-OS XML API docs: `https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-panorama-api`
- Operational commands via API: `type=op&cmd=<show><system><resources/></system></show>`
- HA state: `type=op&cmd=<show><high-availability><state/></high-availability></show>`
- TASK-010: First Palo Alto command (policy/NAT match) — client init pattern lives there
- Env vars: `PALO_HOST`, `PALO_API_KEY` (from `.env`)

## Files expected to change

- `app/palo/client.py` — new: shared PAN-OS API client (extracted from TASK-010 if not already done)
- `app/palo/health.py` — new: `/palo health` and `/palo ha` handlers
- `app/webex/command_router.py` — add routing for `/palo health` and `/palo ha`
- `app/security/auth.py` — add `palo.read` permission to `COMMAND_PERMISSIONS`

## Execution order

1. Extract (or create) `app/palo/client.py`:
   ```python
   import os, requests, urllib3
   urllib3.disable_warnings()

   PALO_HOST = os.getenv("PALO_HOST")
   PALO_API_KEY = os.getenv("PALO_API_KEY")

   def palo_op(cmd_xml: str) -> dict:
       """Run a PAN-OS operational command and return the response dict."""
       url = f"https://{PALO_HOST}/api/"
       params = {
           "type": "op",
           "cmd": cmd_xml,
           "key": PALO_API_KEY,
       }
       resp = requests.get(url, params=params, verify=False, timeout=10)
       resp.raise_for_status()
       return resp  # caller parses XML
   ```

2. Create `app/palo/health.py`:
   ```python
   import xml.etree.ElementTree as ET
   from app.palo.client import palo_op

   def get_system_health() -> str:
       resp = palo_op("<show><system><resources/></system></show>")
       # parse uptime, CPU, memory, session counts from XML response
       ...

   def get_ha_state() -> str:
       resp = palo_op("<show><high-availability><state/></high-availability></show>")
       # parse local state, peer state, sync status
       ...
   ```

3. Add `palo.read` to `COMMAND_PERMISSIONS` in `app/security/auth.py`:
   ```python
   "/palo health": "palo.read",
   "/palo ha": "palo.read",
   ```

4. Wire into `command_router.py`:
   ```python
   elif command_lower.startswith("/palo health"):
       from app.palo.health import get_system_health
       response_text = get_system_health()
   elif command_lower.startswith("/palo ha"):
       from app.palo.health import get_ha_state
       response_text = get_ha_state()
   ```

5. Parse XML response fields:
   - Health: uptime string, management CPU %, data plane CPU %, session count, session utilization %
   - HA: `local-info/state` (active/passive), `peer-info/conn-status` (up/down), `group/running-sync` (synchronized/not)

## Sample output

```
🔥 Palo Alto System Health
━━━━━━━━━━━━━━━━━━━━━━━
Uptime:         12 days, 4:22:11
Mgmt CPU:       8%
Data Plane CPU: 14%
Sessions:       42,817 / 262,144 (16%)
```

```
🔥 Palo Alto HA State
━━━━━━━━━━━━━━━━━━━━
Local state:    Active
Peer state:     Passive
Peer reachable: Yes
Config sync:    ✅ Synchronized
Last sync:      2026-05-28 08:12:33
```

## Acceptance criteria

- [ ] `/palo health` returns uptime, CPU, memory, and session utilization
- [ ] `/palo ha` returns local/peer state and sync status
- [ ] Both commands are gated by `palo.read` permission
- [ ] Connection errors return a clean message (no stack traces in Webex)
- [ ] `PALO_HOST` not set → clean startup warning (via TASK-005 env validation)

## Manual verification

1. `/palo health` — confirm live firewall resource data
2. `/palo ha` — confirm active/passive state shown correctly
3. As `user` role → confirm permission denied
4. Set bad `PALO_API_KEY` → confirm clean error message

## Gotchas & learned lessons

- PAN-OS returns XML, not JSON. Use `xml.etree.ElementTree` — it's in stdlib, no extra dep.
- `verify=False` suppresses TLS cert warnings for self-signed firewall certs; `urllib3.disable_warnings()` keeps the log clean.
- API key can be generated via `curl -k -X POST "https://{PALO_HOST}/api/?type=keygen&user=...&password=..."`.
- HA state XML structure differs between PAN-OS 9.x and 10.x — check the `<enabled>` field first.
- Depends on TASK-010 existing (or being done concurrently) for the client pattern.
