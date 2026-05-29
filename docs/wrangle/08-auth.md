# Auth

> **Read.** Auth is SQL-backed per-request: every webhook hit runs a live SQL query to verify the sender exists and is enabled. RBAC is defined but not enforced — role-based command gating is dead code at runtime.

## What's actually here

### Identity check (enforced)

`app/main.py:36-60` calls `is_authorized(sender_email)` before `handle_command()` is called.

`is_authorized()` → `get_user(email)` (`app/security/auth.py:56-110`):
1. Opens a new pyodbc SQL Server connection
2. Queries `dbo.users WHERE LOWER(email) = LOWER(?)` for `email, name, role_name, enabled`
3. Returns `None` if no row or if `enabled = 0`
4. Returns a user dict if found and enabled

If `None`, `is_authorized()` returns `False` and the webhook sends an "Access Denied" message (and optionally an admin room alert), then returns early.

### Role system (defined, not enforced)

Three roles with defined permission sets (`app/security/auth.py:5-15`):

```python
ROLE_PERMISSIONS = {
    "master": ["*"],
    "admin": ["cucm.read", "cucm.health", "network.read"],
    "user":  ["cucm.read"],
}
```

A `COMMAND_PERMISSIONS` dict maps command prefixes to required permissions (`auth.py:18-53`). Helper functions `has_permission()`, `can_run_command()`, `get_command_permission()` are implemented correctly.

**None of these are called from `command_router.py`.** The router calls `handle_command(message_text, sender_email)` but never calls `can_run_command()`. Any authenticated user — regardless of role — can run any command.

### Admin commands

`app/admin/users.py` does its own role check via `require_master(sender_email)` which calls `get_user_role()`. This is the one place RBAC is actually enforced — only `master` role can run `/admin` commands.

### Webhook security

No Webex webhook secret validation. The endpoint accepts any POST to `/webhook` with a valid-looking JSON body and a `data.id` field. A forged request that guesses a valid Webex message ID would be processed.

### Debug logging (always-on PII)

`auth.py:93-98` prints email, name, role, and enabled status to stdout on every successful auth. This is not a debug flag — it runs in production.

## Open questions

- Is `app/data/authorized_users.py` the old auth mechanism that predates the SQL-backed system? It defines `AUTHORIZED_USERS` and `ROLE_PERMISSIONS` but nothing imports it.
