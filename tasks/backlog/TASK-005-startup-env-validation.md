---
id: TASK-005
category: spec
phase: phase-2
status: backlog
---

# TASK-005: Validate env vars at startup

## User story

As a **developer running the bot**, I want a clear error message at startup if required env vars are missing so that I don't debug cryptic Zeep/pyodbc errors 30 seconds into the first CUCM command.

## Why this matters

Today if `CUCM_HOST` is missing, the app starts fine and the error surfaces only when the first CUCM command runs — as a Zeep connection error that doesn't mention "missing env var." Same for SQL Server vars. The only startup-time crash is `WEBEX_BOT_TOKEN` (checked explicitly in `main.py:16-17`). All other required vars are silently `None`.

## Scope

**In scope:**
- Add a startup validation function that checks all required env vars
- Log a clear error listing missing vars and exit (or warn) on start
- Wire it into FastAPI's startup event

**Out of scope:**
- Validating the values (e.g. testing CUCM connectivity at boot) — just check presence
- Adding new env vars

## References

- Current only check: `app/main.py:16-17`
- Env var list: `CLAUDE.md` → "Environment variables"
- Settings file: `app/config/settings.py`

## Files expected to change

- `app/config/settings.py` — add required var list and validation function
- `app/main.py` — call validation on startup event

## Execution order

1. In `app/config/settings.py`, define required vars:
   ```python
   REQUIRED_VARS = [
       "WEBEX_BOT_TOKEN",
       "CUCM_HOST", "CUCM_USERNAME", "CUCM_PASSWORD",
       "CUCM_SSH_USERNAME", "CUCM_SSH_PASSWORD",
       "NETWORK_USERNAME", "NETWORK_PASSWORD",
       "SQL_SERVER", "SQL_DATABASE",
   ]
   ```
   Note: `SQL_USERNAME`/`SQL_PASSWORD` are only required if `SQL_AUTH_MODE=sql` (the default).
2. Add `validate_env()` function that checks each, collects missing, prints a clear summary, and raises `RuntimeError` if any are missing
3. In `app/main.py`, add a FastAPI startup event:
   ```python
   @app.on_event("startup")
   async def startup():
       from app.config.settings import validate_env
       validate_env()
   ```
4. Test: remove `CUCM_HOST` from `.env`, start app, confirm clear error message

## Acceptance criteria

- [ ] Starting the app with a missing required var logs a clear message naming the missing var(s)
- [ ] App exits (or logs a warning) on missing vars rather than starting silently
- [ ] With all vars present, app starts normally
- [ ] `SQL_USERNAME`/`SQL_PASSWORD` only required when `SQL_AUTH_MODE=sql`

## Manual verification

1. Temporarily comment out `CUCM_HOST=` in `.env`
2. `uvicorn app.main:app` — expect clear startup error naming `CUCM_HOST` as missing
3. Restore `.env`, restart — app boots normally

## Gotchas & learned lessons

- `@app.on_event("startup")` is the FastAPI way; `lifespan` context manager is the newer approach in FastAPI 0.93+ but either works.
- Don't test connectivity at startup — just check for presence. Testing CUCM connectivity adds 5–30 seconds to boot time.
- `BOT_ADMIN_ROOM_ID` is optional (bot works without admin room alerts) — don't require it.
