# CLAUDE.md

Working context for Claude Code sessions on this repo. Read this
before making non-trivial changes.

> This file is **project-specific**. It overrides and extends the
> generic foundation in `.claude/task-rules.md`. The kit's `/sync` will never
> overwrite this file — it's yours to evolve.

## 🪡 Auto-loaded primitives

Claude Code follows `@`-imports here. The kit ships a set of small
primitive files that should be loaded on every session — leave the
imports below in place unless you've removed the corresponding
file. Delete a line if the file isn't used in this project.

@.claude/welcome.md
@.claude/pact.md
@.claude/mode.md
@.claude/bookmarks.md
@.claude/wont-do.md
@docs/notes/INDEX.md

*Why each one:*
- **`welcome.md`** — first-thing context: where you left off, what's
  in flight. Auto-updated by `/handoff`.
- **`pact.md`** — your working-relationship preferences with Claude.
  Portable across repos.
- **`mode.md`** — currently-active work mode (a *drive*, not a
  filter). Only present when a mode is active. When loaded, its
  drive prose shapes Claude's appetite for the session. Switch with
  `/mode <name>`; clear with `/mode normal`. See the kit's
  `kit/modes/README.md` for the concept.
- **`bookmarks.md`** — curated `path:line` pointers for fast
  orientation.
- **`wont-do.md`** — anti-feature list. Stops relitigating closed
  conversations.
- **`docs/notes/INDEX.md`** — rolling index of `/lessons` notes.
  Future Claude sessions read prior learnings on session start.

**Project terminology overrides.** Define any project-specific
meanings of kit terms in `.claude/vocabulary-overrides.md`. Defaults
are in `.claude/vocabulary.md`.

## What this is

Drummond NetOps Bot is a Webex bot that gives Drummond's IT and
network team a chat-driven interface for network operations tasks.
Authorized users can query Cisco CUCM (phone inventory, SIP trunks,
call flow, dial plan, health checks), run basic network commands
(ping, show version via SSH), and manage user access — all from
Webex. The service runs as a FastAPI app receiving Webex webhooks
and routing incoming messages to the appropriate handler.

## Vision

Become the unified chat-driven operations interface for Drummond's
network team, reducing reliance on manual CLI sessions and the CUCM
GUI. At maturity every common NetOps query — phone lookup, trunk
status, DID routing, firewall policy — is answerable in Webex
without leaving the chat window, and the bot handles routine admin
tasks so the team spends less time on repetitive lookups.

## Goal

**Current goal.** Get core CUCM commands stable and reliable, then
expand coverage to Palo Alto firewall queries. Done when `/cucm *`
commands return accurate data consistently and at least one Palo
Alto command is wired up.

**Set.** 2026-05-27

### Achieved

- 2026-05-27 — User auth, basic CUCM commands (phones, trunks, call
  flow, route plan, dial plan, health, phones-eol), and Webex
  webhook handler working end-to-end.

## Platform

**Platform:** python

Agents read `.claude/web-task-rules.md` and `.claude/web-conventions.md`
only if working on the Webex integration layer. Otherwise use the
universal `.claude/task-rules.md` and Python conventions.

## Macro architecture (orchestrator)

**Orchestrator path:** `n/a — solo project`

## Tech stack

- Python 3.9 (`.venv`)
- FastAPI 0.128 + uvicorn — HTTP server and webhook receiver
- Webex Teams SDK (`webexteamssdk`) — send/receive Webex messages
- Zeep — SOAP client for CUCM AXL API (schema under `schema/15.0/`)
- Netmiko — SSH to network devices (ping relay, show version)
- pyodbc + ODBC Driver 18 for SQL Server — direct CUCM database queries
- python-dotenv — env var loading from `.env`
- PyJWT — token handling in auth layer

## Commands

One runtime (`app`). No cloud stamp yet — deploy details below.

| Action | Command |
|---|---|
| **Dev server** | `uvicorn app.main:app --reload` |
| **Register Webex webhook** | `python create_webhook.py` |
| **Install deps** | `pip install -r requirements.txt` |
| **List runtimes** | `ls .claude/runtimes/` |
| **List clouds** | `ls .claude/clouds/` |

No automated test suite yet — verification is manual (send commands
to the bot in Webex and confirm responses).

## Toolchain pinning

- Python 3.9 (`.venv/pyvenv.cfg`)
- ODBC Driver 18 for SQL Server must be installed on the host
  (`brew install unixodbc` on macOS, then the Microsoft ODBC driver)

## Folder layout

```
app/
  main.py              FastAPI entry point; webhook receiver and auth gate
  webex/
    command_router.py  Routes incoming Webex message text to handlers
    help.py            /help command text
  cucm/                CUCM command handlers
    call_flow.py       /cucm call-flow
    css.py             Calling Search Space queries
    dbreplication.py   DB replication status (used by health)
    dial_plan.py       /cucm route (dial plan match)
    did_utils.py       DID lookup helpers
    free_extensions.py /cucm free-extension
    health.py          /cucm health
    phones.py          /cucm phone
    phones_eol.py      /cucm phones-eol (interactive multi-step)
    risport.py         RIS port (registration status) queries
    route_pattern_details.py
    route_plan.py      Route plan builder
    route_plan_lookup.py /cucm route-plan
    trunk_status.py    SIP trunk registration status
    trunks.py          /cucm trunk
  network/
    ping.py            /ping — ICMP ping relay
    show_version.py    /show version — SSH via Netmiko
  admin/
    users.py           /admin user commands (add/remove/list authorized users)
  data/                Static reference data (no DB dependency)
    authorized_users.py
    cucm_nodes.py
    did_blocks.py
    model_lookup.py    Phone model → display name mapping
    phone_eol_catalog.py  EOL dates per model
    sites.py
    trunks.py
  database/
    sql.py             pyodbc connection factory (SQL Server)
  security/
    auth.py            is_authorized() check; unauthorized_message()
  state/
    pending_actions.py In-memory dict for multi-step interactive flows
  config/
    settings.py        BOT_NAME, BOT_VERSION, BOT_ENVIRONMENT
  palo/                Palo Alto integration (stub — in progress)
  utils/               Shared utilities
schema/
  15.0/                Cisco AXL WSDL + XSD (Cisco-owned, do not edit)
scripts/               One-off utility scripts
create_webhook.py      Webex webhook registration helper
requirements.txt
.env                   All secrets and config (never commit)
```

## Schema ownership

This project **consumes** Cisco's AXL SOAP schema under `schema/15.0/`
(`AXLAPI.wsdl`, `AXLSoap.xsd`, `AXLEnums.xsd`). Cisco owns it.
Do not hand-edit these files. Update by downloading a new schema
bundle from Cisco DevNet and replacing the directory wholesale.

## Schema registry

`app/data/` is the canonical registry for static reference data:
sites, trunk definitions, DID blocks, phone model catalog, and EOL
dates. Any new static dataset goes in a new file there — do not
embed raw data in handler files.

## Gated files (project-specific extensions)

- `schema/15.0/` — Cisco-owned; replace wholesale, never hand-edit
- `.env` — secrets; never commit or log values
- `app/data/authorized_users.py` — access control list; changes
  require explicit intent

## Local dev

1. Copy `.env.example` (or create `.env`) and fill in all variables
   listed in the **Environment variables** section below.
2. Install ODBC Driver 18 for SQL Server on your host.
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload` — runs on port 8000.
5. Point the Webex webhook at your public URL + `/webhook`. For
   local dev, use `ngrok http 8000` and run `python create_webhook.py`.

## Environment variables

All vars are required unless noted. Values live in `.env` (never committed).

| Variable | Purpose |
|---|---|
| `WEBEX_BOT_TOKEN` | Webex bot access token |
| `BOT_ADMIN_ROOM_ID` | Webex room ID for unauthorized-access alerts |
| `BOT_NAME` | Display name (default: "Drummond NetOps Bot") |
| `BOT_VERSION` | Version string (default: "0.1.0") |
| `BOT_ENVIRONMENT` | Environment label (default: "Development") |
| `CUCM_HOST` | CUCM publisher hostname/IP (AXL + SSH target) |
| `CUCM_USERNAME` | CUCM AXL API username |
| `CUCM_PASSWORD` | CUCM AXL API password |
| `CUCM_SSH_USERNAME` | CUCM SSH username (for DB replication checks) |
| `CUCM_SSH_PASSWORD` | CUCM SSH password |
| `NETWORK_USERNAME` | SSH username for network devices |
| `NETWORK_PASSWORD` | SSH password for network devices |
| `SQL_SERVER` | SQL Server hostname/IP (CUCM Informix bridge) |
| `SQL_DATABASE` | Database name |
| `SQL_USERNAME` | SQL auth username (ignored if SQL_AUTH_MODE=windows) |
| `SQL_PASSWORD` | SQL auth password (ignored if SQL_AUTH_MODE=windows) |
| `SQL_AUTH_MODE` | `sql` (default) or `windows` |

## Test infrastructure

No automated test suite yet. Manual testing: send commands to the
bot in a Webex space and verify responses match expected output.

For multi-step flows (e.g. `/cucm phones-eol`), verify the full
interaction loop: initial command → numbered list → selection → detail
report.

## Deploy

The bot must be reachable at a public HTTPS URL for Webex to deliver
webhooks. In production, run uvicorn behind a reverse proxy (nginx,
Caddy) or deploy to a cloud host with a stable URL.

Register or update the Webex webhook after any URL change:
`python create_webhook.py`

No cloud stamp exists yet — create `.claude/clouds/` entries when
a permanent hosting target is chosen.

## Conventions

- **Command routing** — all Webex command dispatch lives in
  `app/webex/command_router.py`. New commands are added there as
  `elif command_lower.startswith(...)` blocks. Keep the file ordered:
  help → admin → status → network → CUCM → catch-all.
- **Multi-step interactions** — use `app/state/pending_actions.py`
  (in-memory dict keyed by `sender_email`) for any command that
  needs a follow-up reply from the user. See `phones_eol.py` for
  the pattern.
- **Static reference data** — live in `app/data/`. Handler files
  import from there; never embed raw lists or dicts in handlers.
- **Auth** — every inbound webhook is checked by `is_authorized()`
  before any command runs. Unauthorized attempts are blocked and
  logged to `BOT_ADMIN_ROOM_ID`.
- **AXL queries** — use Zeep with the schema at `schema/15.0/`. See
  existing CUCM handlers for the client initialization pattern.
- **SQL queries** — use `get_sql_connection()` from
  `app/database/sql.py`. Always close the connection after use.

## Pause points / open questions

- `app/palo/` is a stub — Palo Alto integration not yet started.
- No automated tests or CI pipeline in place.
- No permanent hosting target chosen yet (no cloud stamp).
- `app/utils/` is empty — utilities not yet extracted.
- `SQL_AUTH_MODE=windows` path is untested on macOS dev machines.
