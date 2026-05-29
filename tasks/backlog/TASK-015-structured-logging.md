---
id: TASK-015
category: spec
phase: phase-3
status: backlog
---

# TASK-015: Replace print() with structured logging

## User story

As a **bot operator**, I want all application output to go through Python's `logging` module so I can control log level, route to a file, and search structured output — instead of reading a mixed stream of debug prints, auth info, and real errors from stdout.

## Why this matters

The codebase has 30+ `print()` calls scattered across handlers, auth, and database code. They all land on stdout with no level, no timestamp, no context. In production, this means stdout captures everything from "Attempting SQL connection..." to "❌ SQL CONNECTION FAILED" with no way to filter. Python's `logging` module is already available — it just hasn't been wired up.

## Scope

**In scope:**
- Configure a root logger in `app/main.py` at startup
- Replace every `print()` in `app/` with the appropriate `logging.*()` call
- Log levels: `DEBUG` for connection attempts/auth details, `INFO` for request lifecycle, `WARNING` for soft failures, `ERROR`/`EXCEPTION` for caught exceptions
- Log format: `[LEVEL] [timestamp] module: message`

**Out of scope:**
- Shipping logs to an external service (Datadog, CloudWatch, etc.)
- Log rotation (handled by the OS/systemd)
- Structured JSON logging

## References

- Print calls identified in: `app/security/auth.py`, `app/database/sql.py`, `app/cucm/dbreplication.py`, `app/network/show_version.py`, every handler's except block
- FastAPI startup hook: `app/main.py`

## Files expected to change

- `app/main.py` — configure root logger at startup
- `app/security/auth.py` — replace print block with logging
- `app/database/sql.py` — replace "Attempting SQL connection..." prints
- `app/cucm/dbreplication.py` — replace print-based debug output
- All `app/cucm/*.py` — replace except-block prints
- All `app/network/*.py` — replace except-block prints

## Execution order

1. In `app/main.py`, add logger configuration before route registration:
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
       datefmt="%Y-%m-%d %H:%M:%S",
   )
   logger = logging.getLogger("netops")
   ```
2. In each module, add at the top:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```
3. Replace `print("Attempting SQL connection...")` → `logger.debug("SQL connection attempt")`
4. Replace `print("✅ SQL CONNECTION SUCCESSFUL")` → `logger.info("SQL connected")`
5. Replace `print("❌ SQL CONNECTION FAILED")` and `print(f"ERROR: {e}")` → `logger.exception("SQL connection failed")`
6. Replace the AUTH DEBUG block (already removed by TASK-003) — if TASK-003 is not done yet, replace it here instead
7. Replace all `except` block `print()` calls with `logger.exception()`
8. Test: run the app, send a command, confirm clean log output with timestamps and levels

## Acceptance criteria

- [ ] No `print()` calls remain in `app/` (verify with `grep -r "print(" app/`)
- [ ] Log output includes timestamp, level, and module name
- [ ] `DEBUG` level is suppressed by default (INFO threshold)
- [ ] Caught exceptions log a full traceback via `logger.exception()`
- [ ] Setting `LOG_LEVEL=DEBUG` env var enables verbose output

## Manual verification

1. `uvicorn app.main:app --reload`
2. Send `/cucm phone <MAC>` — confirm log line like `2026-05-28 [INFO] app.cucm.phones: phone lookup SEPXXX`
3. Trigger an error (bad CUCM_HOST) — confirm traceback in logs, clean message in Webex

## Gotchas & learned lessons

- `logging.basicConfig()` must be called before any `getLogger()` calls that log. Call it early in `main.py`.
- `logger.exception()` logs at ERROR level and automatically includes the current exception traceback — use it inside `except` blocks.
- `LOG_LEVEL` env var: `logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))` makes it configurable without a code change.
