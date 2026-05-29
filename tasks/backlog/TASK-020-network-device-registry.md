---
id: TASK-020
category: spec
phase: phase-5
status: backlog
---

# TASK-020: Named network device registry

## User story

As a **network engineer**, I want to refer to switches and routers by their hostname (`CORE-SW1`, `DIST-SW-BLDGA`) instead of raw IP addresses when running network commands, so I don't need to memorize or look up management IPs before every query.

## Why this matters

Today's network commands (`/ping`, `/show version`) take raw IP addresses. As TASK-012 and TASK-021 through TASK-024 expand the network command surface, forcing users to type IPs creates friction and errors. A static registry in `app/data/network_devices.py` (consistent with how `app/data/trunks.py` and `app/data/sites.py` work) gives every device a canonical name that resolves to its management IP and SSH profile.

## Scope

**In scope:**
- `app/data/network_devices.py` — static registry of named network devices
- Resolver function `resolve_device(name_or_ip)` that accepts either a name or raw IP and returns connection params
- Update `/show version` (and later: `/ping`, `/show interface`, etc.) to accept device name or IP interchangeably
- `/net devices` — list all registered devices

**Out of scope:**
- Dynamic discovery (SNMP walk, CDP harvest)
- IPAM integration
- Auto-updating the registry from the network

## References

- Pattern to follow: `app/data/trunks.py` and `app/data/sites.py` (static Python dicts)
- Current `/show version` handler: `app/network/show_version.py`
- Env vars: `NETWORK_USERNAME`, `NETWORK_PASSWORD` (already used by show_version.py)

## Files expected to change

- `app/data/network_devices.py` — new: device registry
- `app/network/device_resolver.py` — new: `resolve_device()` helper
- `app/network/show_version.py` — accept name or IP via resolver
- `app/webex/command_router.py` — add `/net devices` listing command

## Execution order

1. Create `app/data/network_devices.py`:
   ```python
   # Network device registry
   # Keys are canonical names (uppercase, consistent with site conventions).
   # device_type: Netmiko device type string.
   # group: logical group for /net devices listing.

   NETWORK_DEVICES = {
       "CORE-SW1": {
           "host": "10.10.1.10",
           "device_type": "cisco_ios",
           "group": "core",
           "description": "Core distribution switch",
       },
       "CORE-SW2": {
           "host": "10.10.1.11",
           "device_type": "cisco_ios",
           "group": "core",
           "description": "Core distribution switch (secondary)",
       },
       # Add site access switches, routers, etc.
   }
   ```

2. Create `app/network/device_resolver.py`:
   ```python
   import ipaddress
   from app.data.network_devices import NETWORK_DEVICES

   def resolve_device(name_or_ip: str) -> dict:
       """
       Accept a device name (case-insensitive) or raw IP.
       Returns a dict with 'host', 'device_type', 'name'.
       Raises ValueError if name not found and input is not a valid IP.
       """
       key = name_or_ip.upper()
       if key in NETWORK_DEVICES:
           entry = NETWORK_DEVICES[key].copy()
           entry["name"] = key
           return entry
       # Try raw IP
       try:
           ipaddress.ip_address(name_or_ip)
           return {"host": name_or_ip, "device_type": "cisco_ios", "name": name_or_ip}
       except ValueError:
           raise ValueError(f"Unknown device: `{name_or_ip}`. Try `/net devices` to list available devices.")
   ```

3. Update `app/network/show_version.py` to use `resolve_device()`:
   ```python
   from app.network.device_resolver import resolve_device

   def show_version(target: str) -> str:
       try:
           device = resolve_device(target)
       except ValueError as e:
           return str(e)
       # use device["host"] for Netmiko connection
       ...
   ```

4. Add `/net devices` to `command_router.py`:
   ```python
   elif command_lower.startswith("/net devices"):
       from app.data.network_devices import NETWORK_DEVICES
       lines = ["📡 **Registered Network Devices**\n"]
       by_group = {}
       for name, info in NETWORK_DEVICES.items():
           by_group.setdefault(info["group"], []).append((name, info))
       for group, devices in sorted(by_group.items()):
           lines.append(f"**{group.upper()}**")
           for name, info in devices:
               lines.append(f"  `{name}` — {info['host']} ({info['description']})")
       response_text = "\n".join(lines)
   ```

5. Add `"network.read"` permission for `/net devices` in `COMMAND_PERMISSIONS`.

## Sample output

```
📡 Registered Network Devices

CORE
  `CORE-SW1` — 10.10.1.10 (Core distribution switch)
  `CORE-SW2` — 10.10.1.11 (Core distribution switch (secondary))

ACCESS
  `ACC-BLDGA-1` — 10.10.2.10 (Building A access switch floor 1)
  `ACC-BLDGA-2` — 10.10.2.11 (Building A access switch floor 2)

WAN
  `ROUTER-1` — 10.10.0.1 (WAN edge router)
```

## Acceptance criteria

- [ ] `/net devices` lists all registered devices grouped by category
- [ ] `/show version CORE-SW1` resolves to the correct IP and returns version info
- [ ] `/show version 10.10.1.10` (raw IP) still works as before
- [ ] Unknown name returns "Unknown device" with a pointer to `/net devices`
- [ ] `app/data/network_devices.py` is the single place to add a new device

## Manual verification

1. `/net devices` — confirm list matches known infrastructure
2. `/show version CORE-SW1` — confirm same result as `/show version 10.10.1.10`
3. `/show version BOGUS-SW` — confirm clean error message

## Gotchas & learned lessons

- Keep device names short and uppercase — they'll be typed in Webex regularly.
- `device_type` matters for Netmiko: `cisco_ios` for IOS/IOS-XE, `cisco_nxos` for Nexus, `cisco_xr` for IOS-XR. Don't default everything to `cisco_ios` if the environment is mixed.
- Raw-IP fallback is important — ops staff sometimes paste IPs directly, especially during incidents when they don't want to look up a name.
- The registry is static (no DB). When a device is added, the file is edited and the service restarted. That's fine — this is a low-churn list.
