# Build, deploy, environments

> **Read.** No build step, no CI/CD, no production hosting target yet. Deployment is manual: run uvicorn, register the Webex webhook with create_webhook.py. The only documented non-local run was via ngrok.

## What's actually here

### Running the app

```sh
# Development (with auto-reload)
uvicorn app.main:app --reload

# Production (no reload)
uvicorn app.main:app
```

No Dockerfile, no systemd unit file, no process manager config in the repo. The `build/` directory was scaffolded by claude-kit and contains the deploy pipeline shell scripts, but no project-specific deploy commands have been filled in yet (`build/deploy` is the kit template).

### Registering the Webex webhook

```sh
python create_webhook.py
```

This script creates a new Webex webhook pointing to the URL hardcoded at `create_webhook.py:17`. That URL (`https://d094-45-22-149-30.ngrok-free.app/webhook`) is a development ngrok session — it changes every time ngrok restarts. The script has no `--update` mode; re-running it creates a duplicate webhook without removing the old one.

### Environment config

All secrets and config in `.env`. No `.env.example` or `.env-template` to document required vars. See `CLAUDE.md` → "Environment variables" for the full list.

### Environments

No staging/production distinction. No `BOT_ENVIRONMENT` logic beyond a label in the `/status` command response.

### Dependencies

```sh
pip install -r requirements.txt
```

Requires ODBC Driver 18 for SQL Server installed on the host OS (`brew install unixodbc` + Microsoft ODBC driver on macOS).

## Open questions

- Where will the bot be permanently hosted?
- How will the Webex webhook URL be managed when the host or URL changes?
- No rollback mechanism — if a deploy breaks something, the only path is to SSH back and restart the process.
