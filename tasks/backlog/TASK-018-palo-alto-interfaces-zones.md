---
id: TASK-018
category: spec
phase: phase-4
status: backlog
---

# TASK-018: Palo Alto interface, zone & route info

## User story

As a **network engineer**, I want to query interface status, zone membership, and the route table on the Palo Alto from Webex so I can troubleshoot connectivity without opening the firewall GUI or a CLI session.

## Why this matters

During a network incident, the three most common firewall data points are: "is this interface up?", "what zone is it in?", and "does the firewall have a route to this destination?". All three are answerable via the PAN-OS XML API operational commands and can be delivered in Webex in seconds.

## Scope

**In scope:**
- `/palo interfaces` — summary of all interfaces (name, IP, state, zone)
- `/palo route <destination>` — look up the forwarding table entry for an IP
- `/palo zones` — list all security zones and their member interfaces

**Out of scope:**
- Modifying interface config
- Route redistribution details
- Virtual router config

## References

- PAN-OS XML API: `https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-panorama-api`
- Interface status: `<show><interface>all</interface></show>`
- Route lookup: `<show><routing><fib><dst>X.X.X.X</dst></fib></routing></show>`
- Zone info: `<show><zone></zone></show>`
- Client: `app/palo/client.py` (from TASK-017)
- Env vars: `PALO_HOST`, `PALO_API_KEY`

## Files expected to change

- `app/palo/interfaces.py` — new: interface, zone, and route handlers
- `app/webex/command_router.py` — add routing for three new `/palo` subcommands
- `app/security/auth.py` — `/palo interfaces`, `/palo zones`, `/palo route` → `palo.read`

## Execution order

1. Create `app/palo/interfaces.py` with three functions:
   ```python
   from app.palo.client import palo_op
   import xml.etree.ElementTree as ET

   def get_interfaces() -> str: ...
   def get_zones() -> str: ...
   def get_route(destination: str) -> str: ...
   ```

2. `get_interfaces()`:
   - Op cmd: `<show><interface>all</interface></show>`
   - Parse each `<entry>` for: `name`, `ip`, `state` (up/down), `zone`
   - Format as a compact table (one line per interface)

3. `get_zones()`:
   - Op cmd: `<show><zone></zone></show>`
   - Parse zone names and their member interfaces
   - Group output by zone

4. `get_route(destination)`:
   - Op cmd: `<show><routing><fib><dst>{destination}</dst></fib></routing></show>`
   - Parse: destination prefix, nexthop, interface, metric
   - If no route found, return "No route to {destination}"
   - Validate `destination` is a valid IPv4 address before sending

5. Add to `COMMAND_PERMISSIONS`:
   ```python
   "/palo interfaces": "palo.read",
   "/palo zones": "palo.read",
   "/palo route": "palo.read",
   ```

6. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/palo interfaces"):
       from app.palo.interfaces import get_interfaces
       response_text = get_interfaces()
   elif command_lower.startswith("/palo zones"):
       from app.palo.interfaces import get_zones
       response_text = get_zones()
   elif command_lower.startswith("/palo route"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/palo route <destination-ip>`"
       else:
           from app.palo.interfaces import get_route
           response_text = get_route(parts[2])
   ```

## Sample output

```
🔥 Palo Alto Interfaces
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interface    IP               State  Zone
ethernet1/1  10.10.1.1/30     up     outside
ethernet1/2  192.168.1.1/24   up     inside
ethernet1/3  172.16.0.1/30    up     dmz
loopback.1   10.255.255.1/32  up     mgmt
```

```
🔥 Route Lookup: 8.8.8.8
━━━━━━━━━━━━━━━━━━━━━━━━
Destination: 0.0.0.0/0 (default)
Next hop:    10.10.1.2
Interface:   ethernet1/1
Metric:      10
```

## Acceptance criteria

- [ ] `/palo interfaces` lists all interfaces with IP, state, and zone
- [ ] `/palo zones` lists all zones and their member interfaces
- [ ] `/palo route 8.8.8.8` returns the matching FIB entry
- [ ] `/palo route` (no arg) returns usage string
- [ ] Invalid IP input returns a clean error (not an API exception)
- [ ] All three commands gated by `palo.read`

## Manual verification

1. `/palo interfaces` — verify interface list matches GUI
2. `/palo zones` — verify zone names match security policy zones
3. `/palo route 8.8.8.8` — confirm default route nexthop shown
4. `/palo route` (no arg) — confirm usage message

## Gotchas & learned lessons

- Interface XML from PAN-OS can have `<ifnet>` or `<hw>` subtrees depending on interface type. Parse `<ifnet>` for logical interfaces.
- Zone membership comes from config, not operational state — may need `type=config` query instead of `type=op` for zone data.
- FIB lookup (`fib`) is per-virtual-router. Default VR is `default`. Add the VR name to the command if the firewall has multiple VRs.
- Validate IP input with `ipaddress.ip_address()` before sending to the API — PAN-OS returns a generic fault on bad input.
