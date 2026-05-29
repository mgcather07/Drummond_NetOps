---
id: TASK-010
category: spec
phase: phase-3
status: backlog
---

# TASK-010: Palo Alto first commands (policy + NAT)

## User story

As a **network engineer**, I want to ask the bot whether a given source IP can reach a destination IP/port and what NAT rule applies, without logging into the Palo Alto GUI.

## Why this matters

`app/palo/` is an empty stub. Palo Alto firewall queries are the stated next expansion goal in `CLAUDE.md`. The two highest-value first commands for a network team are: (1) "does a policy allow this traffic?" and (2) "what NAT rule applies to this IP?" — both answerable via the PAN-OS REST API without making changes to the firewall.

## Scope

**In scope:**
- `/palo policy <src-ip> <dst-ip> <port>` — run a security policy test and return the matching rule name and action (allow/deny)
- `/palo nat <ip>` — return the NAT rule that applies to the given IP
- New env vars: `PALO_HOST`, `PALO_API_KEY` (or `PALO_USERNAME`/`PALO_PASSWORD`)
- Wire both commands into `command_router.py`

**Out of scope:**
- Making any firewall changes
- `/palo health`, `/palo interface` (future tasks)
- Multi-firewall support (single firewall for now)

## References

- PAN-OS REST API test security policy: `https://{host}/api/?type=op&cmd=<test><security-policy-match>...`
- PAN-OS REST API key generation: `https://{host}/api/?type=keygen&user=&password=`
- Existing CUCM handler pattern to follow: `app/cucm/phones.py`
- Command router: `app/webex/command_router.py`

## Files expected to change

- `app/palo/__init__.py` — create (empty)
- `app/palo/policy.py` — new: `/palo policy` handler
- `app/palo/nat.py` — new: `/palo nat` handler
- `app/webex/command_router.py` — add Palo Alto command dispatch block
- `app/webex/help.py` — add Palo Alto section to `CUCM_HELP` or a new `PALO_HELP`
- `.env` — add `PALO_HOST`, `PALO_API_KEY`
- `app/config/settings.py` (or `TASK-005` validation) — add Palo Alto vars to required list

## Execution order

1. Generate a PAN-OS API key:
   ```sh
   curl -k "https://$PALO_HOST/api/?type=keygen&user=$PALO_USERNAME&password=$PALO_PASSWORD"
   ```
   Add result to `.env` as `PALO_API_KEY`
2. Create `app/palo/__init__.py` (empty)
3. Create `app/palo/policy.py` — implement `/palo policy <src> <dst> <port>`:
   - Call PAN-OS `test security-policy-match` XML API
   - Parse the XML response for `rules/entry/@name` and action
   - Return formatted result
4. Create `app/palo/nat.py` — implement `/palo nat <ip>`:
   - Call PAN-OS `show running nat-policy` or `test nat-policy-match` XML API
   - Parse for matching NAT rule name and translation
   - Return formatted result
5. Add imports and dispatch to `command_router.py`:
   ```python
   if command_lower.startswith("/palo policy"):
       return get_policy_match(command)
   if command_lower.startswith("/palo nat"):
       return get_nat_match(command)
   ```
6. Add `PALO_HOST` to `TASK-005` env validation (or add now if TASK-005 is not yet done)
7. Add `/help palo` section to `help.py`
8. Manual verification against live firewall

## Acceptance criteria

- [ ] `/palo policy 10.0.1.50 8.8.8.8 443` returns the matching policy rule name and action
- [ ] `/palo nat 10.0.1.50` returns the applicable NAT rule (or "no NAT rule found")
- [ ] Both commands are accessible only to `admin`/`master` roles (update `COMMAND_PERMISSIONS` in `auth.py`)
- [ ] `/help palo` lists the new commands
- [ ] Firewall unreachable returns a clear error, not a traceback

## Manual verification

1. `/palo policy <known-internal-ip> 8.8.8.8 443` — confirm returns expected rule
2. `/palo nat <internal-ip-with-known-NAT>` — confirm correct NAT rule returned
3. `/palo policy` (no args) — confirm usage message returned

## Gotchas & learned lessons

- PAN-OS XML API requires `verify=False` for self-signed certs (same as CUCM). Suppress urllib3 warnings.
- The `test security-policy-match` command requires specifying protocol number, not just port — TCP=6, UDP=17.
- API key auth is preferred over username/password per-request. Generate once, store in `.env`.
- Add `COMMAND_PERMISSIONS` entries in `auth.py` for `/palo policy` and `/palo nat` (suggest `network.read` permission or a new `palo.read`).

## Open questions / risks

- Does Drummond have a single Palo Alto or multiple (HA pair, multiple firewalls)? If HA pair, target the active node.
- Is the PAN-OS management interface reachable from wherever the bot runs?
- What PAN-OS version is in use? API responses vary slightly across versions.
