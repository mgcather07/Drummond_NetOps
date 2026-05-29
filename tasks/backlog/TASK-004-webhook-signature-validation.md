---
id: TASK-004
category: spec
phase: phase-1
status: backlog
---

# TASK-004: Add Webex webhook signature validation

## User story

As a **bot operator**, I want the webhook endpoint to validate Webex's HMAC signature so that forged HTTP requests cannot trigger bot commands.

## Why this matters

`POST /webhook` currently accepts any correctly-shaped JSON POST. Webex supports a `secret` field when creating a webhook — when set, Webex includes an `X-Spark-Signature` header (HMAC-SHA1 of the raw request body using the secret). Without validating this header, any actor who can reach the endpoint and guess a valid Webex message ID can trigger bot processing.

## Scope

**In scope:**
- Add `WEBEX_WEBHOOK_SECRET` env var
- Validate `X-Spark-Signature` in the webhook handler
- Return HTTP 401 for invalid signatures
- Update `create_webhook.py` to pass the secret when creating/updating the webhook

**Out of scope:**
- Changing any command routing or auth logic

## References

- Webex webhook signature docs: https://developer.webex.com/docs/api/guides/webhooks#handling-requests-from-webex
- Handler: `app/main.py:26-84`
- Webhook registration: `create_webhook.py`

## Files expected to change

- `app/main.py` — add signature validation at the top of `webhook()`
- `create_webhook.py` — pass `secret=WEBEX_WEBHOOK_SECRET` to `webhooks.create()`
- `.env` — add `WEBEX_WEBHOOK_SECRET=<value>` (not committed)

## Execution order

1. Generate a random secret string (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`) and add to `.env` as `WEBEX_WEBHOOK_SECRET`
2. Add `WEBEX_WEBHOOK_SECRET` to `app/main.py` env loading
3. In `webhook()`, read the raw request body before parsing JSON:
   ```python
   body = await request.body()
   signature = request.headers.get("X-Spark-Signature", "")
   expected = hmac.new(
       WEBHOOK_SECRET.encode(),
       body,
       hashlib.sha1
   ).hexdigest()
   if not hmac.compare_digest(signature, expected):
       return JSONResponse({"status": "invalid signature"}, status_code=401)
   data = json.loads(body)
   ```
4. Update `create_webhook.py` to read `WEBEX_WEBHOOK_SECRET` from env and pass `secret=...` to `webhooks.create()`
5. Re-register the webhook: `python create_webhook.py`
6. Send a real Webex message — confirm bot responds normally
7. Send a forged POST (curl with wrong/missing signature) — confirm 401

## Acceptance criteria

- [ ] `WEBEX_WEBHOOK_SECRET` is read from env in `main.py`
- [ ] Requests without `X-Spark-Signature` return 401
- [ ] Requests with a wrong signature return 401
- [ ] Real Webex webhook requests (with correct signature) are processed normally
- [ ] `create_webhook.py` passes the secret when registering

## Manual verification

1. Send a real command from Webex — bot responds correctly
2. `curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{"data":{"id":"fake"}}'` — expect 401
3. Check Webex webhook registration includes a secret

## Gotchas & learned lessons

- **Read raw body before JSON parsing.** FastAPI's `await request.json()` consumes the body stream. Use `await request.body()` first, then `json.loads(body)`.
- **Use `hmac.compare_digest`** not `==` to prevent timing attacks.
- **If `WEBEX_WEBHOOK_SECRET` is not set**, skip validation (for local dev without a registered webhook). Log a warning.
- **The webhook must be re-registered** with the secret after this change — Webex only adds the signature header if the webhook was created with a secret.

## Open questions / risks

- If `WEBEX_WEBHOOK_SECRET` is missing from `.env`, should the app refuse to start or just skip validation? Recommend: skip validation + warn, to avoid breaking local dev.
