---
id: TASK-021
category: spec
phase: phase-5
status: backlog
---

# TASK-021: ARP table + MAC address table lookup

## User story

As a **network engineer**, I want to look up where an IP or MAC address is currently seen on the network so I can locate a host, confirm it's reachable at Layer 2, and find which switch port it's connected to — all from Webex.

## Why this matters

"Where is this host?" is asked multiple times per day during troubleshooting. Today it requires SSH-ing to the router for ARP and then SSH-ing to every candidate switch for MAC table entries. Wrapping these two commands in Webex reduces a 5-minute multi-hop CLI search to one command.

## Scope

**In scope:**
- `/net arp <device> <ip>` — look up an IP in the ARP table of a specific device (router/L3 switch)
- `/net mac <device> <mac>` — look up a MAC address in the MAC address table of a specific device
- Normalize MAC input (accept `aabb.ccdd.eeff`, `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`)

**Out of scope:**
- Network-wide ARP sweep across all devices (too slow for chat)
- ARP/MAC correlation (finding the port for an IP in one command — do that later as a compound)
- Writing ARP/MAC entries

## References

- Netmiko `send_command()` pattern: `app/network/show_version.py`
- Device resolver: `app/network/device_resolver.py` (TASK-020)
- Commands:
  - IOS/IOS-XE ARP: `show ip arp <ip>`
  - IOS/IOS-XE MAC: `show mac address-table address <mac>`
  - NX-OS ARP: `show ip arp <ip>`
  - NX-OS MAC: `show mac address-table address <mac>`
- Env vars: `NETWORK_USERNAME`, `NETWORK_PASSWORD`

## Files expected to change

- `app/network/arp_mac.py` — new: ARP and MAC lookup handlers
- `app/webex/command_router.py` — add `/net arp` and `/net mac` routing
- `app/security/auth.py` — both commands → `network.read`

## Execution order

1. Create `app/network/arp_mac.py`:
   ```python
   import os, re
   from netmiko import ConnectHandler
   from app.network.device_resolver import resolve_device

   NETWORK_USERNAME = os.getenv("NETWORK_USERNAME")
   NETWORK_PASSWORD = os.getenv("NETWORK_PASSWORD")

   def normalize_mac(mac: str) -> str:
       """Strip separators, return lowercase hex string, then reformat to IOS dotted notation."""
       clean = re.sub(r'[:\-\.]', '', mac).lower()
       if len(clean) != 12:
           raise ValueError(f"Invalid MAC address: `{mac}`")
       return f"{clean[0:4]}.{clean[4:8]}.{clean[8:12]}"

   def arp_lookup(device_name: str, ip: str) -> str: ...
   def mac_lookup(device_name: str, mac: str) -> str: ...
   ```

2. `arp_lookup(device_name, ip)`:
   - Resolve device via `resolve_device(device_name)`
   - SSH via Netmiko, run `show ip arp {ip}`
   - Parse output: IP, MAC, age, interface
   - Return formatted result or "No ARP entry for {ip} on {device_name}"

3. `mac_lookup(device_name, mac)`:
   - Normalize MAC with `normalize_mac()`
   - Resolve device
   - SSH via Netmiko, run `show mac address-table address {mac}`
   - Parse output: VLAN, MAC, type (dynamic/static), port
   - Return formatted result or "MAC {mac} not found on {device_name}"

4. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/net arp"):
       parts = command.split()
       if len(parts) < 4:
           response_text = "Usage: `/net arp <device> <ip>`"
       else:
           from app.network.arp_mac import arp_lookup
           response_text = arp_lookup(parts[2], parts[3])
   elif command_lower.startswith("/net mac"):
       parts = command.split()
       if len(parts) < 4:
           response_text = "Usage: `/net mac <device> <mac>`"
       else:
           from app.network.arp_mac import mac_lookup
           response_text = mac_lookup(parts[2], parts[3])
   ```

5. Add permissions in `auth.py`:
   ```python
   "/net arp": "network.read",
   "/net mac": "network.read",
   ```

## Sample output

```
🔍 ARP Lookup on CORE-SW1
━━━━━━━━━━━━━━━━━━━━━━━━━
IP:        10.10.5.50
MAC:       aabb.ccdd.1234
Age:       2 min
Interface: GigabitEthernet0/1
```

```
🔍 MAC Lookup on ACC-BLDGA-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAC:   aabb.ccdd.1234
VLAN:  100
Type:  dynamic
Port:  GigabitEthernet0/12
```

## Acceptance criteria

- [ ] `/net arp CORE-SW1 10.10.5.50` returns ARP entry with MAC and interface
- [ ] `/net mac ACC-BLDGA-1 aa:bb:cc:dd:12:34` normalizes the MAC and returns port/VLAN
- [ ] All three MAC formats (colon, hyphen, dotted) are accepted
- [ ] No ARP/MAC entry returns a clean "not found" message
- [ ] Invalid MAC format returns a clean validation error
- [ ] Both commands gated by `network.read`

## Manual verification

1. `/net arp CORE-SW1 <known-IP>` — confirm ARP entry matches CLI output
2. `/net mac <access-sw> <known-MAC>` — confirm port/VLAN matches CLI output
3. `/net mac <device> <unknown-MAC>` — confirm clean "not found" response
4. `/net mac <device> badmac` — confirm validation error

## Gotchas & learned lessons

- Netmiko `send_command()` uses `expect_string` internally — long MAC tables on large switches may time out with the default 100-second timeout. Pass `read_timeout=30` to cap it.
- Cisco IOS `show mac address-table` output varies by platform (IOS, NX-OS, IOS-XE). Parse with `textfsm` or a simple regex — don't assume fixed column positions.
- MAC table entries age out quickly (default 300 seconds on IOS). A "not found" result doesn't mean the host doesn't exist — it may have aged out since last traffic.
- The `normalize_mac()` function must handle partial inputs gracefully — return a clear error rather than passing garbage to the switch command.
