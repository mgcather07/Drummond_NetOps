---
id: TASK-014
category: spec
phase: phase-3
status: backlog
---

# TASK-014: Standardized error handling and response format

## User story

As a **bot user**, I want all error responses to have a consistent format so I can immediately tell what failed and why, without reading a Python traceback.

## Why this matters

Error responses today are inconsistent across handlers. Some return a multiline block with `Error Type:` and `Error:` fields. Some return a one-liner. Some leak Python exception class names (`ZeepError`, `ConnectHandler`, `pyodbc.Error`). None follow a shared template. A user seeing `❌ SIP trunk lookup failed. Error Type: zeep.exceptions.Fault Error: ...` gets no actionable information.

## Scope

**In scope:**
- Define a shared error response format in `app/utils/responses.py`
- Apply it consistently across all CUCM, network, and admin handlers
- Translate common exception types into plain-English messages
- Preserve the full error detail in the *log* (not the Webex response)

**Out of scope:**
- Changing any command logic
- Adding retry logic (separate concern)

## References

- Example inconsistent errors: `app/cucm/phones.py:114-121`, `app/cucm/trunks.py:127-134`, `app/network/show_version.py:43-44`
- Utils dir: `app/utils/` (empty — this and TASK-011 are the first additions)

## Files expected to change

- `app/utils/responses.py` — new: shared response helpers
- `app/cucm/*.py` — update except blocks to use shared format
- `app/network/*.py` — update except blocks
- `app/admin/users.py` — update error returns

## Execution order

1. Create `app/utils/responses.py` with:
   ```python
   def error(title: str, detail: str = "", hint: str = "") -> str:
       """Standard bot error response. Detail/hint not shown to user — log them."""
       lines = [f"❌ {title}"]
       if hint:
           lines.append(f"\n💡 {hint}")
       return "\n".join(lines)

   def success(title: str, body: str = "") -> str:
       lines = [f"✅ {title}"]
       if body:
           lines.append(body)
       return "\n".join(lines)
   ```
2. Define a `translate_exception(e)` function mapping common types to plain English:
   - `zeep.exceptions.Fault` → "CUCM AXL returned an error"
   - `requests.exceptions.ConnectionError` → "Could not reach CUCM"
   - `requests.exceptions.Timeout` → "CUCM request timed out"
   - `pyodbc.Error` → "SQL Server connection failed"
   - `NetmikoTimeoutException` → "SSH connection timed out"
   - `NetmikoAuthenticationException` → "SSH authentication failed"
   - Fallback → "Unexpected error"
3. Update every `except Exception as e:` block across CUCM/network handlers to use `error(translate_exception(e), ...)` and log the full exception with `logging.exception()`
4. Test: trigger a CUCM failure (e.g. wrong CUCM_HOST) and confirm user sees a clean message

## Acceptance criteria

- [ ] All `except` blocks in CUCM and network handlers use `error()` from `responses.py`
- [ ] No Python exception class names appear in bot responses
- [ ] Common exceptions (timeout, auth failure, connection error) have plain-English messages
- [ ] Full exception detail is logged, not sent to the user

## Manual verification

1. Set `CUCM_HOST` to a bad IP, run `/cucm phone SEPXXX` — confirm clean error message
2. Set bad SSH creds, run `/show version <ip>` — confirm "SSH authentication failed" style message
3. Check logs — confirm full traceback appears in log output

## Gotchas & learned lessons

- After TASK-015 (logging), `logging.exception()` will land in the log file. For now, `print()` is fine as a placeholder.
- Don't over-specify hint text — "Check that CUCM is reachable" is enough. Don't tell the user to check `.env`.
