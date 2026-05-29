---
id: TASK-019
category: spec
phase: phase-4
status: backlog
---

# TASK-019: Palo Alto address/rule search by IP

## User story

As a **network engineer**, I want to search the Palo Alto security policy by IP address so I can answer "what rules allow traffic to/from this host?" without manually scanning hundreds of policy entries in the GUI.

## Why this matters

Security policy review is one of the most time-consuming manual tasks on a firewall with 200+ rules. A Webex command that returns every rule referencing a given IP (directly or via an address object that contains it) cuts a 10-minute GUI search to a 5-second chat query. This is the last of the four Palo Alto commands — together with TASK-010, TASK-017, TASK-018 they give complete day-to-day operational coverage.

## Scope

**In scope:**
- `/palo search <ip>` — find all security rules that reference the given IP (as source or destination), including rules that reference an address object containing that IP
- `/palo address <name>` — look up a named address object and show its value(s)

**Out of scope:**
- NAT rule search (covered by TASK-010's `/palo nat`)
- Application or service object search
- Config push or rule editing

## References

- PAN-OS XML API config query: `type=config&action=get&xpath=...`
- Security policy xpath: `/config/devices/entry/vsys/entry/rulebase/security/rules`
- Address objects xpath: `/config/devices/entry/vsys/entry/address`
- Client: `app/palo/client.py` (from TASK-017)
- Env vars: `PALO_HOST`, `PALO_API_KEY`

## Files expected to change

- `app/palo/search.py` — new: address object lookup and rule search
- `app/webex/command_router.py` — add `/palo search` and `/palo address`
- `app/security/auth.py` — both commands → `palo.read`

## Execution order

1. Add a config-query helper to `app/palo/client.py`:
   ```python
   def palo_config_get(xpath: str) -> str:
       """Fetch a config subtree by XPath. Returns raw XML string."""
       url = f"https://{PALO_HOST}/api/"
       params = {
           "type": "config",
           "action": "get",
           "xpath": xpath,
           "key": PALO_API_KEY,
       }
       resp = requests.get(url, params=params, verify=False, timeout=15)
       resp.raise_for_status()
       return resp.text
   ```

2. Create `app/palo/search.py`:
   ```python
   import xml.etree.ElementTree as ET
   import ipaddress
   from app.palo.client import palo_config_get

   ADDRESS_XPATH = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address"
   SECURITY_XPATH = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/security/rules"

   def get_address_object(name: str) -> str: ...
   def search_rules_by_ip(ip: str) -> str: ...
   ```

3. `get_address_object(name)`:
   - Fetch all address objects, find by `name` attribute
   - Show: object name, type (ip-netmask / ip-range / fqdn), value, any tags
   - Case-insensitive match; if not found return "No address object named `{name}`"

4. `search_rules_by_ip(ip)`:
   - Fetch all address objects → build a dict mapping `{object_name: [contained_cidrs]}`
   - Fetch all security rules
   - For each rule, collect source and destination members (direct IPs + address object names)
   - Expand address object names to their CIDR values
   - Match: include rule if the target IP falls within any source or destination CIDR
   - Return matching rules: name, zone-from → zone-to, source, destination, application, action (allow/deny)

5. Wire in `command_router.py`:
   ```python
   elif command_lower.startswith("/palo search"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/palo search <ip-address>`"
       else:
           from app.palo.search import search_rules_by_ip
           response_text = search_rules_by_ip(parts[2])
   elif command_lower.startswith("/palo address"):
       parts = command.split()
       if len(parts) < 3:
           response_text = "Usage: `/palo address <object-name>`"
       else:
           from app.palo.search import get_address_object
           response_text = get_address_object(parts[2])
   ```

## Sample output

```
🔍 Rules referencing 10.10.5.50
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rule: Allow-CUCM-to-SQL
  From:   inside → dmz
  Source: CUCM-Servers (contains 10.10.5.0/24) ✓
  Dest:   SQL-Server
  App:    mssql
  Action: ✅ allow

Rule: Deny-All-Outbound
  From:   inside → outside
  Source: any
  Dest:   any
  App:    any
  Action: ❌ deny

2 rules found.
```

```
📦 Address Object: CUCM-Servers
  Type:  ip-netmask
  Value: 10.10.5.0/24
  Tags:  cucm, voice
```

## Acceptance criteria

- [ ] `/palo search 10.10.5.50` returns all security rules that apply to that IP
- [ ] Rules referencing an address object that contains the IP are included (not just direct IP matches)
- [ ] `/palo address CUCM-Servers` returns the object name, type, and value
- [ ] No-arg usage returns usage string for both commands
- [ ] Both commands gated by `palo.read`
- [ ] Results are truncated gracefully if > 20 rules match (show count + first 20)

## Manual verification

1. `/palo search <known-host-IP>` — verify rules match what GUI shows
2. `/palo search <IP-in-address-object>` — verify object expansion works
3. `/palo address <known-object-name>` — verify value matches GUI
4. `/palo search` (no arg) — confirm usage string

## Gotchas & learned lessons

- The device/vsys names in the XPath (`localhost.localdomain`, `vsys1`) are the defaults for a standalone firewall. Multi-vsys deployments will differ — parameterize or make configurable via env var.
- Address object expansion can be slow if there are 500+ objects. Fetch once and cache for the session, or time-limit to 15s.
- `ip-range` type objects (e.g. `10.0.0.1-10.0.0.50`) need range membership check, not just CIDR containment. Use `ipaddress` stdlib for CIDR; write a simple range check for ip-range.
- `any` source/destination always matches — include those rules in results with a note.
- Palo Alto rule names can contain spaces — don't split on spaces when parsing rule names from XML attributes.
