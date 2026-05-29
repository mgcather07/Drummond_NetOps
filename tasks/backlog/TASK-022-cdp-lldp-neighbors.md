---
id: TASK-022
category: spec
phase: phase-5
status: backlog
---

# TASK-022: CDP/LLDP neighbor discovery

## User story

As a **network engineer**, I want to see what devices are physically connected to a switch or router from Webex so I can trace topology and confirm physical cabling without CLI access.

## Why this matters

CDP/LLDP neighbor tables are the fastest way to understand physical topology. During a troubleshooting session ("what's connected to port Gi0/12?") or a move/add/change ("where does this uplink go?"), this command eliminates a CLI hop. Combined with TASK-021 (MAC lookup), it gives Layer 1 + Layer 2 visibility in chat.

## Scope

**In scope:**
- `/net neighbors <device>` — CDP and LLDP neighbor summary for all ports
- `/net neighbors <device> <interface>` — neighbor detail for a specific interface
- Prefer CDP output; fall back to LLDP if CDP returns nothing

**Out of scope:**
- Recursive topology mapping (graphing the full network)
- Writing neighbor entries

## References

- Netmiko pattern: `app/network/show_version.py`
- Device resolver: `app/network/device_resolver.py` (TASK-020)
- Commands:
  - CDP: `show cdp neighbors detail` (all), `show cdp neighbors {interface} detail` (specific port)
  - LLDP: `show lldp neighbors detail`
- Env vars: `NETWORK_USERNAME`, `NETWORK_PASSWORD`

## Files expected to change

- `app/network/neighbors.py` — new: CDP/LLDP neighbor discovery
- `app/webex/command_router.py` — add `/net neighbors` routing
- `app/security/auth.py` — `network.read` permission

## Execution order

1. Create `app/network/neighbors.py`:
   ```python
   import os
   from netmiko import ConnectHandler
   from app.network.device_resolver import resolve_device

   NETWORK_USERNAME = os.getenv("NETWORK_USERNAME")
   NETWORK_PASSWORD = os.getenv("NETWORK_PASSWORD")

   def get_neighbors(device_name: str, interface: str = None) -> str: ...
   def _parse_cdp_detail(raw: str) -> list[dict]: ...
   def _parse_lldp_detail(raw: str) -> list[dict]: ...
   ```

2. `get_neighbors(device_name, interface)`:
   - Resolve device
   - Run `show cdp neighbors detail` (or `show cdp neighbors {interface} detail` if interface given)
   - If output contains "CDP is not enabled" or 0 entries, try `show lldp neighbors detail`
   - Parse with `_parse_cdp_detail()` or `_parse_lldp_detail()`
   - Format and return

3. `_parse_cdp_detail(raw)`:
   - Split on `-------------------------` delimiter between neighbor entries
   - For each entry extract: device ID, local interface, remote interface, platform, IP
   - Return list of dicts

4. `_parse_lldp_detail(raw)`:
   - Split on `------------------------------------------------` or similar
   - Extract: system name, local port, remote port, system description, management IP

5. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/net neighbors"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/net neighbors <device> [interface]`"
       else:
           device = parts[2]
           iface = parts[3] if len(parts) > 3 else None
           from app.network.neighbors import get_neighbors
           response_text = get_neighbors(device, iface)
   ```

6. Add `"/net neighbors": "network.read"` to `COMMAND_PERMISSIONS`.

## Sample output

```
📡 CDP Neighbors on CORE-SW1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Local Port       Remote Device     Remote Port   Platform       IP
Gi0/1 (uplink)  WAN-ROUTER-1      Gi0/0         CISCO2911      10.10.0.1
Gi0/2            ACC-BLDGA-1       Gi0/25        WS-C2960X      10.10.2.10
Gi0/3            ACC-BLDGB-1       Gi0/25        WS-C2960X      10.10.3.10

3 neighbors found (via CDP).
```

```
📡 CDP Neighbor on CORE-SW1 Gi0/2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Device ID:    ACC-BLDGA-1
Local port:   GigabitEthernet0/2
Remote port:  GigabitEthernet0/25
Platform:     cisco WS-C2960X-24TS-L
IP address:   10.10.2.10
```

## Acceptance criteria

- [ ] `/net neighbors CORE-SW1` returns all CDP neighbors with local/remote ports and IPs
- [ ] `/net neighbors CORE-SW1 Gi0/2` returns detail for that specific port
- [ ] Falls back to LLDP if CDP returns 0 neighbors
- [ ] No-arg usage returns usage string
- [ ] Command gated by `network.read`
- [ ] Truncated gracefully if > 20 neighbors (show count, first 20)

## Manual verification

1. `/net neighbors CORE-SW1` — compare to `show cdp neighbors` in CLI
2. `/net neighbors CORE-SW1 Gi0/2` — verify remote device and port match CLI
3. On an LLDP-only device — confirm fallback works

## Gotchas & learned lessons

- CDP neighbor detail output is notoriously inconsistent between IOS versions. Use `re.search()` with named groups rather than fixed-line parsing.
- `show cdp neighbors` (brief) vs `show cdp neighbors detail` — the brief form lacks IP and platform. Always use `detail`.
- Interface abbreviation normalization: user might type `Gi0/2`, `GigabitEthernet0/2`, or `gi0/2`. Pass the user's string directly to the command — IOS accepts abbreviations.
- On large switches (48-port with all ports populated), the `detail` output can be thousands of lines. Set `read_timeout=60`.
- If CDP is globally disabled (privacy policy), the fallback to LLDP is essential. Check both protocols in all environments.
