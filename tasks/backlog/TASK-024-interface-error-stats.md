---
id: TASK-024
category: spec
phase: phase-5
status: backlog
---

# TASK-024: Interface error and utilization stats

## User story

As a **network engineer**, I want to check interface error counters and utilization on a specific port from Webex so I can diagnose flapping links, CRC errors, or congestion without opening a CLI session.

## Why this matters

Interface errors (CRC, input/output drops, resets) are a leading indicator of physical layer problems, duplex mismatches, and congestion. During an incident, checking these counters is one of the first diagnostic steps. Surfacing them in Webex eliminates the SSH hop and makes the data accessible to anyone on the team, not just those with SSH credentials.

## Scope

**In scope:**
- `/net stats <device> <interface>` — show input/output rates, error counters, and link state for a specific interface
- Flag high error rates with a warning indicator (> 0 CRC or > 100 drops)

**Out of scope:**
- SNMP polling or time-series graphing
- Clearing counters (write operation — exclude for safety)
- Aggregate stats across all interfaces

## References

- Netmiko pattern: `app/network/show_version.py`
- Device resolver: `app/network/device_resolver.py` (TASK-020)
- Command: `show interfaces {interface}` (IOS/IOS-XE)
- Env vars: `NETWORK_USERNAME`, `NETWORK_PASSWORD`

## Files expected to change

- `app/network/stats.py` — new: interface error and utilization handler
- `app/webex/command_router.py` — add `/net stats` routing
- `app/security/auth.py` — `network.read` permission

## Execution order

1. Create `app/network/stats.py`:
   ```python
   import os, re
   from netmiko import ConnectHandler
   from app.network.device_resolver import resolve_device

   NETWORK_USERNAME = os.getenv("NETWORK_USERNAME")
   NETWORK_PASSWORD = os.getenv("NETWORK_PASSWORD")

   def get_interface_stats(device_name: str, interface: str) -> str: ...
   def _parse_interface(raw: str) -> dict: ...
   def _flag(value: int, threshold: int) -> str:
       return "⚠️" if value > threshold else ""
   ```

2. `_parse_interface(raw)` — extract from `show interfaces` output:
   - Line protocol state: `{interface} is {admin-state}, line protocol is {proto-state}`
   - Speed/duplex: `BW {bps} Kbit/sec`, `Full-duplex` or `Half-duplex`
   - Input rate: `5 minute input rate {bps} bits/sec, {pps} packets/sec`
   - Output rate: `5 minute output rate {bps} bits/sec, {pps} packets/sec`
   - Input errors: `{n} input errors, {crc} CRC, {frame} frame`
   - Output drops: `{n} output drops`
   - Input drops: `{n} input drops`
   - Last clearing: `Last clearing of "show interface" counters {time}`

3. Format with warning flags:
   - CRC > 0 → `⚠️` next to CRC count
   - Input drops > 100 → `⚠️` next to input drops
   - Output drops > 100 → `⚠️` next to output drops
   - Line protocol down → `❌` next to state

4. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/net stats"):
       parts = command.split()
       if len(parts) < 4:
           response_text = "Usage: `/net stats <device> <interface>`"
       else:
           from app.network.stats import get_interface_stats
           response_text = get_interface_stats(parts[2], parts[3])
   ```

5. Add `"/net stats": "network.read"` to `COMMAND_PERMISSIONS`.

## Sample output

```
📊 Interface Stats: CORE-SW1 GigabitEthernet0/1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State:         up / line protocol up
Speed:         1000 Mbps, Full-duplex

Input rate:    142 Kbps (187 pps)
Output rate:   89 Kbps (112 pps)

Input errors:  0
CRC errors:    0
Input drops:   0
Output drops:  0 ⚠️  (threshold: >100)

Last cleared:  never
```

*(Example with errors:)*
```
📊 Interface Stats: ACC-BLDGA-1 GigabitEthernet0/12
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State:         up / line protocol up
Speed:         100 Mbps, Half-duplex ⚠️

Input rate:    8 Kbps (12 pps)
Output rate:   2 Kbps (4 pps)

Input errors:  1,842
CRC errors:    1,839 ⚠️
Input drops:   0
Output drops:  0

Last cleared:  00:47:12 ago
```

## Acceptance criteria

- [ ] `/net stats CORE-SW1 Gi0/1` returns link state, speed, rate, and error counters
- [ ] CRC errors > 0 are flagged with `⚠️`
- [ ] Input/output drops > 100 are flagged with `⚠️`
- [ ] Interface not found on device returns a clean error message
- [ ] Missing arg returns usage string
- [ ] Command gated by `network.read`

## Manual verification

1. `/net stats CORE-SW1 Gi0/1` — compare to `show interfaces Gi0/1` CLI output
2. On a known problem port with CRC errors — confirm `⚠️` flag appears
3. `/net stats CORE-SW1 Gi9/99` — confirm "interface not found" response
4. `/net stats` (no args) — confirm usage string

## Gotchas & learned lessons

- `show interfaces {interface}` output on IOS has the interface name on the first line and all counters below. The exact line format varies between IOS versions and interface types (SVI vs physical). Use regex with `.search()`, not line-position parsing.
- Half-duplex at 100 Mbps is almost always a duplex mismatch — flag it as a warning in the output.
- "Last clearing" being `never` is normal on stable interfaces. Don't flag it as an error.
- Interface names: users type `Gi0/1`, `GigabitEthernet0/1`, or `gi0/1`. IOS accepts abbreviations — pass through directly.
- On NX-OS, the command is `show interface {interface}` (no `s`) and counter field names differ. Handle both if NX-OS devices are in the registry.
