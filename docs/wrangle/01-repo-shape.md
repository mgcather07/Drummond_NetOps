# Repo shape & entry points

> **Read.** A single-process Python FastAPI app (~4,000 lines across ~30 files) that acts as a Webex bot webhook receiver, routing chat commands to Cisco CUCM and network device queries.

## What's actually here

The repo has one runnable process: the FastAPI app defined in `app/main.py`. There are no background workers, no separate CLIs, and no subpackages beyond the single `app/` tree.

Top-level layout:

```
app/
  main.py              FastAPI entry point; registers GET / and POST /webhook
  webex/               Webex command dispatch and help text
  cucm/                All CUCM command handlers (~14 files)
  network/             Ping and SSH show-version
  admin/               User CRUD against SQL Server
  data/                Static reference data (sites, trunks, DID blocks, models, EOL catalog)
  database/            pyodbc SQL Server connection factory
  security/            Auth: SQL-backed user lookup + RBAC definitions
  state/               In-memory pending-action dict for multi-step flows
  config/              BOT_NAME / VERSION / ENVIRONMENT from env
  palo/                Empty stub — Palo Alto integration not started
  utils/               Empty — nothing extracted yet
schema/
  15.0/                Cisco AXL WSDL + XSD (Cisco-owned schema consumed by Zeep)
scripts/               Empty
create_webhook.py      One-off Webex webhook registration script
requirements.txt       Pin file (Python 3.9, managed with pip)
.env                   All secrets and config (not committed)
```

The `schema/15.0/` directory is the Cisco AXL WSDL bundle that Zeep loads at runtime to know the CUCM SOAP API shape. It is Cisco-owned and should not be hand-edited.

## How it fits

`app/main.py` is the only entry point and the only file with route decorators. Everything else is called from the webhook handler. `create_webhook.py` is a one-shot script that must be run separately to register the Webex webhook URL.

## Open questions

- Why does `app/data/authorized_users.py` exist? Nothing imports it. See `12-smells-and-risks.md`.
