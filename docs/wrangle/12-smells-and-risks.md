# Smells & risks

> **Read.** Ten verified concerns. Items 1–3 are highest priority (security / data integrity). Items 4–10 are reliability and maintainability risks.

## 🔴 High priority

**1. RBAC is defined but not enforced — all authenticated users can run all commands.**
`app/security/auth.py` defines `ROLE_PERMISSIONS`, `COMMAND_PERMISSIONS`, `has_permission()`, and `can_run_command()`. None of these are called from `app/webex/command_router.py`. The only gate is "is the user in the DB at all." A `user`-role account can run `/cucm health`, `/ping`, and admin commands (except `/admin` which has its own `require_master()` check).
- `app/security/auth.py:113-114` — `is_authorized` returns True for any enabled user regardless of role
- `app/webex/command_router.py` — no `can_run_command()` call anywhere

**2. No Webex webhook signature validation.**
The `/webhook` endpoint (`app/main.py:26`) accepts any POST. Webex supports a `secret` parameter on webhooks that allows HMAC-SHA1 validation of the `X-Spark-Signature` header. Without this, any actor who can POST to the endpoint with a valid-looking payload could trigger bot commands if they know or can guess a valid Webex message ID.

**3. `app/data/authorized_users.py` is dead code that creates a false sense of an access control list.**
The file defines `AUTHORIZED_USERS` with three real email addresses and `ROLE_PERMISSIONS`. Nothing in the codebase imports it. The live auth system is `app/security/auth.py` + `dbo.users`. A developer reading the repo might trust this file as the actual user list — it is not.
- `app/data/authorized_users.py:1-34` — not imported anywhere

## 🟠 Reliability risks

**4. Auth SQL query opens a new connection on every request — no connection pooling.**
`get_user()` calls `get_sql_connection()` which calls `pyodbc.connect()` fresh each time. For a low-traffic internal tool this is fine. Under load (or if the SQL Server is slow), this will become a bottleneck. Every command that reaches auth also makes additional SQL calls (admin commands make 1–3 more).
- `app/database/sql.py:14` — `pyodbc.connect()` with no pool

**5. `PENDING_ACTIONS` is a process-scoped in-memory dict with no TTL.**
If a user starts `/cucm phones-eol` and never replies with a selection number, their entry stays in `PENDING_ACTIONS` forever (until the process restarts). If they later type any number in chat it will be misinterpreted as a phone model selection.
- `app/state/pending_actions.py:24` — `PENDING_ACTIONS = {}`
- `app/cucm/phones_eol.py:202` — pending entry set with no expiry

**6. Webhook handler is `async def` but all I/O is blocking.**
`app/main.py:29` — the webhook handler is declared async, but calls Webex API (`messages.get`), SQL Server (`get_sql_connection`), and potentially Netmiko SSH (for CUCM health check, up to 120 seconds). These block the event loop. Uvicorn runs async handlers, so long-running commands will block other incoming requests.

**7. RISPort WSDL is fetched from the live CUCM server on every call.**
`app/cucm/risport.py:27` — `wsdl = f"https://{CUCM_HOST}:8443/..."`. Zeep fetches this WSDL at client creation time, which is inside every phone status or trunk status call. If CUCM is slow or unreachable, the WSDL fetch itself adds latency/failure before the actual query runs. AXL uses a local WSDL file; RISPort should too.

## 🟡 Maintainability risks

**8. Hardcoded ngrok URL in `create_webhook.py:17`.**
`targetUrl="https://d094-45-22-149-30.ngrok-free.app/webhook"` — this is a development URL that changes when ngrok restarts. Running this script without updating the URL will create a broken webhook. There's no `--update` mode; re-running creates duplicate webhooks.

**9. Auth debug PII is always logged to stdout.**
`app/security/auth.py:93-98` prints the user's email, name, role, and enabled status on every successful auth check. There is no log level or debug flag — this runs in production and logs PII to whatever captures stdout.
```python
print("========== AUTH DEBUG ==========")
print(f"EMAIL: {row.email}")
print(f"NAME: {row.name}")
...
```

**10. `/ping` passes user input directly to `subprocess.run` without sanitization.**
`app/network/ping.py:12-18` — `target = parts[1]` passed directly as the fourth element of `["ping", "-c", "4", target]`. Because this uses `subprocess.run` with a list (not a shell string), shell injection is not possible. However, a user can ping internal network segments or cause the process to block for 10 seconds per attempt with a slow host.
