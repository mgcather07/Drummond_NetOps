---
id: TASK-003
category: spec
phase: phase-1
status: backlog
---

# TASK-003: Remove always-on PII debug logging

## User story

As a **bot operator**, I want user PII (email, name, role) not printed to stdout on every request so that logs don't accumulate sensitive data in plaintext.

## Why this matters

`app/security/auth.py:93-98` unconditionally prints `EMAIL`, `NAME`, `ROLE`, and `ENABLED` to stdout on every successful auth check. This is not gated by a debug flag. Every Webex message processed logs PII to whatever captures stdout (terminal, log file, systemd journal, cloud logging service). This is a data hygiene issue that will matter when the bot is hosted permanently.

## Scope

**In scope:**
- Remove or replace the debug print block in `auth.py`
- Optionally replace with a structured debug log gated on an env var

**Out of scope:**
- Adding a full logging framework
- Changing any other logging in the codebase

## References

- Offending code: `app/security/auth.py:91-98`

```python
print("========== AUTH DEBUG ==========")
print(f"EMAIL: {row.email}")
print(f"NAME: {row.name}")
print(f"ROLE: {row.role_name}")
print(f"ENABLED: {row.enabled}")
print("================================")
```

## Files expected to change

- `app/security/auth.py` — remove the debug print block

## Execution order

1. Open `app/security/auth.py`
2. Delete lines 91-98 (the `AUTH DEBUG` print block)
3. Optionally replace with: `print(f"AUTH: {row.email} role={row.role_name}")` gated on `os.getenv("DEBUG_AUTH")` if some auth logging is desired
4. Restart the app and send a test command — confirm no PII printed to terminal

## Acceptance criteria

- [ ] Sending a Webex command does not print email, name, or role to stdout
- [ ] App still authenticates users correctly (auth logic is unchanged)
- [ ] `get_user()` still returns the correct user dict

## Manual verification

1. `uvicorn app.main:app --reload`
2. Send any command from an authorized Webex account
3. Confirm terminal does not print `AUTH DEBUG` block
4. Confirm bot replies correctly (auth still works)

## Gotchas & learned lessons

- The auth logic (SQL query, enabled check, return dict) must not be touched — only the print statements.

## Open questions / risks

- Do you want any auth logging at all? If yes, gate it on `DEBUG_AUTH=true` env var so it's opt-in.
