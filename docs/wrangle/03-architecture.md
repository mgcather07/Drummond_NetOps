# Architecture & module boundaries

> **Read.** Five clean layers — HTTP, routing, handlers, data, auth — with one notable gap: the RBAC layer (defined in `auth.py`) is not connected to the routing layer, so role-based command gating is not enforced at runtime.

## What's actually here

```
┌─────────────────────────────────────────────┐
│  HTTP Layer                                  │
│  app/main.py — FastAPI, POST /webhook        │
└───────────────────┬─────────────────────────┘
                    │ auth gate (is_authorized)
┌───────────────────▼─────────────────────────┐
│  Routing Layer                               │
│  app/webex/command_router.py                 │
│  Dispatches on command_lower prefix          │
└───┬──────────────┬──────────────┬────────────┘
    │              │              │
┌───▼───┐    ┌────▼────┐   ┌────▼────┐
│ cucm/ │    │network/ │   │ admin/  │
│ ~14   │    │  ping   │   │ users   │
│ files │    │ showver │   │  CRUD   │
└───┬───┘    └────┬────┘   └────┬────┘
    │              │              │
┌───▼──────────────▼──────────────▼────────────┐
│  Data Layer                                   │
│  app/database/sql.py  — SQL Server (users)    │
│  CUCM AXL SOAP        — phones, trunks, plans │
│  CUCM RISPort SOAP    — live device status    │
│  CUCM SSH (Netmiko)   — db replication        │
│  Network SSH (Netmiko)— show version          │
│  app/data/*.py        — static reference data │
└───────────────────────────────────────────────┘
```

**HTTP layer** (`app/main.py`): Receives Webex webhook POST. Fetches the full message from the Webex API (Webex webhooks only send the message ID, not the body). Runs `is_authorized()` — a live SQL call per request. Calls `handle_command()`. Sends the reply. All of this is synchronous inside `async def webhook`.

**Routing layer** (`app/webex/command_router.py`): Strips bot mention prefix, normalizes to lowercase, runs pending-action check first, then dispatches on `command_lower.startswith(...)`. The order matters: help → admin → status → network → CUCM → catch-all. No framework routing — it's a chain of `if/elif`.

**Handler layer** (`app/cucm/`, `app/network/`, `app/admin/`): Each file handles one logical command. Most CUCM handlers follow the same pattern: build a Zeep client with `schema/15.0/AXLAPI.wsdl`, create the AXL service binding, call one or two AXL methods or run `executeSQLQuery`, format the result as a string.

**Data layer**: See `05-data-layer.md`.

**Auth layer** (`app/security/auth.py`): Defines `is_authorized()`, `has_permission()`, `can_run_command()`, and `ROLE_PERMISSIONS`/`COMMAND_PERMISSIONS`. Only `is_authorized()` is called at runtime (in `main.py`). The RBAC functions exist but are not wired into the routing layer.

**State layer** (`app/state/pending_actions.py`): Module-level `PENDING_ACTIONS = {}` dict. Stores per-user pending interactive state (e.g., waiting for a model selection number after `/cucm phones-eol`). Process-scoped, no TTL.

## How it fits

The layers are clean and there is little cross-layer leakage. The biggest architectural gap is the RBAC system existing in `auth.py` without being enforced in `command_router.py`. See `12-smells-and-risks.md` item 10.
