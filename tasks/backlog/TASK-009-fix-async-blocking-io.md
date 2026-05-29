---
id: TASK-009
category: spec
phase: phase-2
status: backlog
---

# TASK-009: Move blocking I/O off async event loop

## User story

As a **bot operator**, I want the webhook handler to not block uvicorn's event loop during slow CUCM or SQL operations so that concurrent requests are processed without queuing.

## Why this matters

`app/main.py:29` declares `async def webhook(request: Request)` but every code path inside it is blocking: `webex_api.messages.get()` (HTTP), `is_authorized()` (SQL), `handle_command()` (CUCM SOAP / SSH — up to 120 seconds for health check). This blocks uvicorn's event loop for the duration of each request. A second Webex message arriving while a `/cucm health` check is running will queue until the first completes.

## Scope

**In scope:**
- Wrap `handle_command()` in `asyncio.get_event_loop().run_in_executor(None, ...)` to run it in a thread pool
- Optionally wrap `webex_api.messages.get()` and `is_authorized()` the same way

**Out of scope:**
- Rewriting handlers to be natively async
- Adding a task queue (Redis/Celery)
- Supporting parallel execution of multiple CUCM commands

## References

- Handler: `app/main.py:29-84`
- Python docs: `asyncio.loop.run_in_executor()` — https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor

## Files expected to change

- `app/main.py` — wrap blocking calls in `run_in_executor`

## Execution order

1. Add `import asyncio` to `app/main.py` imports
2. Replace the `handle_command()` call with:
   ```python
   loop = asyncio.get_event_loop()
   reply = await loop.run_in_executor(
       None,
       handle_command,
       message.text,
       sender_email,
   )
   ```
3. Optionally wrap `webex_api.messages.get(message_id)` similarly:
   ```python
   message = await loop.run_in_executor(None, webex_api.messages.get, message_id)
   ```
4. Test with two concurrent requests: send `/cucm health` (slow) and `/status` (instant) in quick succession — `/status` should return immediately while health is running

## Acceptance criteria

- [ ] `handle_command()` runs in a thread pool executor, not the event loop
- [ ] A fast command (`/status`) responds immediately while a slow command (`/cucm health`) is in flight
- [ ] No change to command behavior or response format

## Manual verification

1. Send `/cucm health` from one Webex account (triggers 30–60 second CUCM operations)
2. Immediately send `/status` from a second account (or same account)
3. `/status` response should arrive before `/cucm health` completes

## Gotchas & learned lessons

- `PENDING_ACTIONS` is a module-level dict accessed from the thread pool. Python's GIL makes simple dict reads/writes thread-safe for CPython, but be aware if this ever becomes more complex.
- `asyncio.get_event_loop()` is deprecated in newer Python in favor of `asyncio.get_running_loop()`. Use `asyncio.get_running_loop()` inside an async function.
- The default `ThreadPoolExecutor` has `min(32, os.cpu_count() + 4)` threads — fine for this use case.

## Open questions / risks

- If the uvicorn worker count is increased beyond 1 in future, `PENDING_ACTIONS` (process-scoped) will not be shared between workers. That's a separate task (TASK-007 TTL is the first mitigation).
