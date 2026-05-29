---
id: TASK-001
category: spec
phase: phase-1
status: backlog
---

# TASK-001: Wire RBAC into command router

## User story

As a **bot admin**, I want role-based command gating enforced so that `user`-role accounts can only run CUCM read commands, `admin`-role accounts can also run health and network commands, and only `master` can manage users.

## Why this matters

The RBAC system is fully implemented in `app/security/auth.py` — `ROLE_PERMISSIONS`, `COMMAND_PERMISSIONS`, `has_permission()`, `can_run_command()` — but `command_router.py` never calls it. Today every authenticated user can run every command regardless of role. This was verified by reading `app/webex/command_router.py` — no call to `can_run_command()` exists anywhere in the file.

## Scope

**In scope:**
- Add a `can_run_command()` check in `command_router.py` after the pending-action check
- Return the existing `command_permission_denied_message()` when the check fails
- Verify the `COMMAND_PERMISSIONS` map in `auth.py` covers all current commands

**Out of scope:**
- Changing how roles are defined or stored
- Adding new roles
- Modifying the SQL user table

## References

- Auth module: `app/security/auth.py:135-169` — `has_permission()`, `can_run_command()`, `command_permission_denied_message()`
- Router: `app/webex/command_router.py:17-125` — where the check needs to be inserted
- Role definitions: `app/security/auth.py:5-53` — `ROLE_PERMISSIONS` and `COMMAND_PERMISSIONS`

## Files expected to change

- `app/webex/command_router.py` — add permission check
- `app/security/auth.py` — audit `COMMAND_PERMISSIONS` for missing entries (read-only if already complete)

## Execution order

1. Read `app/security/auth.py` — confirm `can_run_command()` and `command_permission_denied_message()` signatures
2. Read `app/webex/command_router.py` — identify the right insertion point (after pending-action check, before command dispatch)
3. Add import: `from app.security.auth import can_run_command, command_permission_denied_message`
4. Insert check:
   ```python
   if not can_run_command(sender_email, command):
       return command_permission_denied_message(sender_email, command)
   ```
5. Audit `COMMAND_PERMISSIONS` in `auth.py` — verify every command prefix in `command_router.py` is either covered or intentionally public (`/help`, `/status`)
6. Add any missing entries to `COMMAND_PERMISSIONS`
7. Manual verification (see below)

## Acceptance criteria

- [ ] A `user`-role account cannot run `/cucm health`, `/ping`, or `/show version`
- [ ] A `user`-role account can still run `/cucm phone`, `/cucm trunk`, `/cucm route-plan`, `/cucm route`, `/cucm call-flow`, `/cucm free-extension`, `/cucm phones-eol`
- [ ] An `admin`-role account can run all of the above plus `/cucm health` and `/ping`
- [ ] A `master`-role account can run everything
- [ ] `/help` and `/status` work for all authenticated users regardless of role
- [ ] Denied commands return the existing permission-denied message format

## Manual verification

1. Identify a `user`-role account in `dbo.users`
2. Send `/cucm health` from that account — expect "Permission Denied" response
3. Send `/cucm phone SEPXXX` from that account — expect phone lookup (no denial)
4. Send `/ping 8.8.8.8` from that account — expect "Permission Denied"
5. Repeat with `admin`-role: `/cucm health` should succeed, `/admin users` should fail
6. Confirm `master`-role can run everything

## Gotchas & learned lessons

- **`/cucm phones-eol` selection replies** — when a user replies with a number to select a model, that message hits the pending-action check first (`command_router.py:45-51`). The permission check must come *after* the pending-action check so interactive flows aren't broken mid-session.
- **`/help` is intentionally public** — not in `COMMAND_PERMISSIONS` means `get_command_permission()` returns `None`, which `can_run_command()` treats as "no permission required." This is correct behavior per `auth.py:165-168`.
- **`/status` is also public** — same as above. Do not add it to `COMMAND_PERMISSIONS`.

## Open questions / risks

- Should unauthorized-but-authenticated users get the permission-denied message silently, or should admin room alerts fire? Currently admin room alerts only fire for completely unauthorized users.
