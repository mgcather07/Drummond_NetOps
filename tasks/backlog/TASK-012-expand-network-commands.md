---
id: TASK-012
category: spec
phase: phase-3
status: backlog
---

# TASK-012: Expand network commands (traceroute, show interface, show ip route)

## User story

As a **network engineer**, I want to run traceroute and show interface/route commands from Webex without SSH-ing into a device manually.

## Why this matters

The current network commands (`/ping`, `/show version`) established the SSH pattern via Netmiko. The pattern is identical for additional commands — just different send_command strings. Adding traceroute and show interface gives the team three of the most common day-to-day network diagnosis commands without expanding the architecture at all.

## Scope

**In scope:**
- `/traceroute <target>` — OS-level traceroute from the bot host
- `/show interface <device-ip>` — SSH to device, run `show interfaces`
- `/show ip route <device-ip>` — SSH to device, run `show ip route`

**Out of scope:**
- Per-device credentials (all use shared `NETWORK_USERNAME`/`NETWORK_PASSWORD`)
- Device inventory / named devices (user supplies IP directly, as with `/show version`)
- SSH to non-Cisco-IOS devices (use existing `cisco_ios` device type)

## References

- Existing ping pattern: `app/network/ping.py`
- Existing show version pattern: `app/network/show_version.py`
- Command router: `app/webex/command_router.py`

## Files expected to change

- `app/network/traceroute.py` — new
- `app/network/show_interface.py` — new
- `app/network/show_route.py` — new
- `app/webex/command_router.py` — add dispatch for new commands
- `app/webex/help.py` — update `NETWORK_HELP`
- `app/security/auth.py` — add `COMMAND_PERMISSIONS` entries for new commands

## Execution order

1. Create `app/network/traceroute.py` — same pattern as `ping.py` using `subprocess.run(["traceroute", "-m", "15", target])`. Add a 30-second timeout (traceroute is slower than ping).
2. Create `app/network/show_interface.py` — same pattern as `show_version.py` using `connection.send_command("show interfaces")`. Truncate at 3000 chars.
3. Create `app/network/show_route.py` — same pattern using `connection.send_command("show ip route")`. Truncate at 3000 chars.
4. Add imports and dispatch to `command_router.py` (keep ordering: `/show interface` before `/show ip route` before `/show version` — longer prefix first):
   ```python
   if command_lower.startswith("/traceroute"):
       return traceroute_host(command)
   if command_lower.startswith("/show interface"):
       return show_interface(command)
   if command_lower.startswith("/show ip route"):
       return show_route(command)
   ```
5. Add `network.read` entries to `COMMAND_PERMISSIONS` for all three new commands
6. Update `NETWORK_HELP` in `help.py`
7. Manual verification

## Acceptance criteria

- [ ] `/traceroute 8.8.8.8` returns traceroute output from the bot host
- [ ] `/show interface <device-ip>` returns interface summary from the device
- [ ] `/show ip route <device-ip>` returns routing table from the device
- [ ] All three commands require `network.read` permission (only `admin`/`master`)
- [ ] `/help network` lists all three new commands

## Manual verification

1. `/traceroute 8.8.8.8` — confirm hops returned
2. `/show interface <known-device-ip>` — confirm interface list returned
3. `/show ip route <known-device-ip>` — confirm route table returned
4. Send `/show interface` (no args) — confirm usage message

## Gotchas & learned lessons

- **`/show interface` vs `/show interfaces`** — CUCM boxes won't have these. These commands target network switches/routers. Make sure test device is an IOS device.
- **Command prefix ordering matters** in `command_router.py`. `/show interface` must come before `/show version` in the if-chain or it will never match (since `/show version` also starts with `/show`). Actually looking at the current code, `/show version` is matched with `command_lower.startswith("/show version")` — the new prefixes (`/show interface`, `/show ip route`) won't collide, but keep the order explicit.
- **Traceroute timeout** — `traceroute` on macOS uses UDP by default and may need `-I` for ICMP. Linux is ICMP by default. Check what OS the bot runs on.
- Truncate `show interfaces` output — on a large switch it can be thousands of lines.
