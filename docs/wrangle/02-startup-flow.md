# Startup flow

> **Read.** Process startup is a linear four-step boot: load env → init Webex client → register routes → hand off to uvicorn. No lazy init; if `WEBEX_BOT_TOKEN` is absent, the process crashes before the first request.

## What's actually here

Startup sequence when `uvicorn app.main:app` is run (`app/main.py:1-21`):

1. **`load_dotenv()`** — reads `.env` into `os.environ`. No validation beyond `BOT_TOKEN` presence.
2. **`BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")`** — if `None`, raises `ValueError` immediately and process exits.
3. **`ADMIN_ROOM_ID = os.getenv("BOT_ADMIN_ROOM_ID")`** — no crash if missing; alerting to the admin room just silently skips.
4. **`webex_api = WebexTeamsAPI(access_token=BOT_TOKEN)`** — single global Webex client. No retry config; no connection pool management.
5. **FastAPI registers two routes** — `GET /` returns a health blob, `POST /webhook` is the main handler.
6. **uvicorn begins accepting connections.**

Other module-level initialization happens lazily when a handler module is first imported (on first matching command), not at startup. This means a bad `CUCM_HOST` won't surface until the first CUCM command runs.

## How it fits

The global `webex_api` object is used only in `main.py`. Handler modules each create their own Zeep/Netmiko/pyodbc connections per-request — there is no shared connection pool.

## Open questions

- CUCM env vars (`CUCM_HOST`, `CUCM_USERNAME`, `CUCM_PASSWORD`) are silently `None` if missing. First CUCM command produces a cryptic Zeep/requests error rather than a startup-time validation failure.
