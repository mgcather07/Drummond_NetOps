---
id: TASK-002
category: spec
phase: phase-1
status: backlog
---

# TASK-002: Delete dead authorized_users.py

## User story

As a **developer reading the codebase**, I want no misleading dead code so that I don't mistake `app/data/authorized_users.py` for the live access control list.

## Why this matters

`app/data/authorized_users.py` defines `AUTHORIZED_USERS` (a dict of real email addresses with roles) and `ROLE_PERMISSIONS`. Nothing in the codebase imports it — verified with grep. The live auth system is `app/security/auth.py` + `dbo.users` in SQL Server. A developer (or future Claude session) reading this file will assume it's the access control list. It is not. Leaving it is a correctness risk.

## Scope

**In scope:**
- Delete `app/data/authorized_users.py`
- Confirm nothing imports it (grep before deleting)

**Out of scope:**
- Changing the live auth system
- Modifying `app/security/auth.py`
- Modifying `dbo.users`

## References

- Dead file: `app/data/authorized_users.py:1-34`
- Live auth: `app/security/auth.py` — the real system
- Wrangle finding: `docs/wrangle/12-smells-and-risks.md` item 3

## Files expected to change

- `app/data/authorized_users.py` — deleted

## Execution order

1. `grep -r "authorized_users" app/` — confirm zero imports
2. Delete `app/data/authorized_users.py`
3. Run the app locally (`uvicorn app.main:app --reload`) — confirm no import errors on startup

## Acceptance criteria

- [ ] `app/data/authorized_users.py` does not exist
- [ ] `grep -r "authorized_users" app/` returns no results
- [ ] App starts cleanly with no import errors

## Manual verification

1. `grep -r "authorized_users" app/` — must return empty
2. `uvicorn app.main:app --reload` — app boots, `GET /` returns 200

## Gotchas & learned lessons

- **Do the grep first.** If something does import it that was missed during the audit, the import error at startup will tell you immediately.

## Open questions / risks

- None. This is safe to do standalone, does not depend on TASK-001.
