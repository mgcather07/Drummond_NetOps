---
id: TASK-006
category: spec
phase: phase-2
status: backlog
---

# TASK-006: Fix create_webhook.py (upsert + env URL)

## User story

As a **developer managing the bot**, I want `create_webhook.py` to update an existing webhook instead of creating duplicates, and to read the target URL from `.env` instead of a hardcoded ngrok address.

## Why this matters

`create_webhook.py:17` has a hardcoded ngrok URL that changes every time ngrok restarts. Re-running the script without updating this URL creates a broken webhook. Worse, running the script multiple times creates duplicate webhooks — Webex will deliver events to all of them, and stale ones point at dead URLs. The fix is: read URL from env, list existing webhooks, update if one named "Drummond NetOps Webhook" exists, create if not.

## Scope

**In scope:**
- Read `WEBHOOK_TARGET_URL` from `.env`
- List existing webhooks and update the named one if it exists (upsert)
- Print the resulting webhook URL and ID for confirmation

**Out of scope:**
- Cleaning up pre-existing duplicate webhooks (one-time manual cleanup)
- TASK-004 webhook secret (coordinate: if TASK-004 is done first, include `secret=` here; if after, add it then)

## References

- Current script: `create_webhook.py:1-26`
- Webex SDK docs: https://webexteamssdk.readthedocs.io/en/latest/user/api.html#webhooks

## Files expected to change

- `create_webhook.py` — full rewrite
- `.env` — add `WEBHOOK_TARGET_URL=https://your-host/webhook`

## Execution order

1. Add `WEBHOOK_TARGET_URL` to `.env`
2. Rewrite `create_webhook.py`:
   ```python
   from webexteamssdk import WebexTeamsAPI
   from dotenv import load_dotenv
   import os

   load_dotenv()

   api = WebexTeamsAPI(access_token=os.getenv("WEBEX_BOT_TOKEN"))
   target_url = os.getenv("WEBHOOK_TARGET_URL")
   webhook_name = "Drummond NetOps Webhook"

   if not target_url:
       raise ValueError("WEBHOOK_TARGET_URL missing from .env")

   existing = [w for w in api.webhooks.list() if w.name == webhook_name]

   if existing:
       webhook = api.webhooks.update(existing[0].id, name=webhook_name, targetUrl=target_url)
       print(f"Updated webhook: {webhook.id} → {webhook.targetUrl}")
   else:
       webhook = api.webhooks.create(name=webhook_name, targetUrl=target_url, resource="messages", event="created")
       print(f"Created webhook: {webhook.id} → {webhook.targetUrl}")
   ```
3. Run the script — confirm correct URL registered
4. Send a test Webex message — confirm bot responds

## Acceptance criteria

- [ ] Script reads target URL from `WEBHOOK_TARGET_URL` env var
- [ ] Running script twice does not create duplicate webhooks
- [ ] Script prints the registered URL and ID on success
- [ ] Missing `WEBHOOK_TARGET_URL` raises a clear error

## Manual verification

1. `python create_webhook.py` — note the webhook ID
2. `python create_webhook.py` again — same webhook ID, not a new one
3. Check Webex developer portal — only one webhook named "Drummond NetOps Webhook"

## Gotchas & learned lessons

- `api.webhooks.list()` returns all webhooks for the bot token. Filter by name.
- If TASK-004 is done first, add `secret=os.getenv("WEBEX_WEBHOOK_SECRET")` to both `create` and `update` calls.
