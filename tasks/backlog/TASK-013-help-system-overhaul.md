---
id: TASK-013
category: spec
phase: phase-3
status: backlog
---

# TASK-013: Help system overhaul — complete and accurate

## User story

As a **bot user**, I want `/help` to show me every available command with correct syntax and a one-line description so I don't have to guess what commands exist or how to call them.

## Why this matters

`app/webex/help.py` is outdated and incomplete. It lists `/ping` but not `/traceroute` (once added). It won't list Palo Alto or vSphere commands once those land. The help categories don't match the role system — a `user`-role account sees help text for `/cucm health` and `/ping` even though they can't run those commands. Every time a new command is added, help must be manually updated, and today that's already drifted.

## Scope

**In scope:**
- Rewrite `help.py` to be the single source of truth for all commands
- Role-aware help: only show commands the calling user's role can actually run
- Category structure: `/help`, `/help cucm`, `/help network`, `/help palo`, `/help vsphere`, `/help admin`
- Syntax documentation: each entry shows the exact call format with args

**Out of scope:**
- Commands not yet implemented (help stubs for future commands)
- Interactive help (clicking a command to run it)

## References

- Current help: `app/webex/help.py`
- Role/command permissions: `app/security/auth.py` — `COMMAND_PERMISSIONS`
- Command router: `app/webex/command_router.py` — source of truth for what's actually wired

## Files expected to change

- `app/webex/help.py` — full rewrite
- `app/security/auth.py` — `get_help_categories_for_role()` helper (or inline in help.py)

## Execution order

1. Audit `command_router.py` — list every real command prefix currently wired
2. Map each command to its required permission (`COMMAND_PERMISSIONS` in `auth.py`)
3. Rewrite `help.py` with a data-driven structure:
   ```python
   COMMANDS = {
       "cucm": [
           ("/cucm phone <MAC>", "cucm.read", "Phone config + live registration status"),
           ("/cucm trunk <alias>", "cucm.read", "SIP trunk config + live status"),
           ...
       ],
       "network": [...],
       "palo": [...],
       "admin": [...],
   }
   ```
4. `get_help(command, sender_email)` — accept `sender_email`, filter commands by `has_permission()`
5. Update `command_router.py` to pass `sender_email` to `get_help()`
6. Test each role: confirm `user` sees only commands they can run

## Acceptance criteria

- [ ] `/help` shows categories available to the calling user's role
- [ ] `/help cucm` lists every wired CUCM command with correct syntax
- [ ] `/help network` lists every wired network command
- [ ] `/help admin` only returns content for `master`-role users
- [ ] A `user`-role account does not see `/cucm health` or `/ping` in any help output
- [ ] Adding a new command requires only adding one entry to `COMMANDS` in `help.py`

## Manual verification

1. `/help` as `user` role — categories visible match role permissions
2. `/help cucm` as `user` — only `cucm.read` commands listed
3. `/help admin` as `user` — "no commands available" or empty section
4. `/help admin` as `master` — full admin command list

## Gotchas & learned lessons

- **Do this after TASK-001 (RBAC)** — role-aware help only makes sense once roles are enforced.
- The help output is sent via `webex_api.messages.create(text=...)` — markdown bold/code will render.
- Keep each command entry to one line in the output. Don't pad with descriptions longer than ~60 chars.
