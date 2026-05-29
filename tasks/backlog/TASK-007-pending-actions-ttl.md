---
id: TASK-007
category: spec
phase: phase-2
status: backlog
---

# TASK-007: Add TTL to PENDING_ACTIONS

## User story

As a **bot user**, I want an incomplete multi-step flow (like `/cucm phones-eol`) to expire after a few minutes so that a forgotten selection doesn't intercept my future messages.

## Why this matters

`PENDING_ACTIONS` is a module-level dict with no expiry. If a user starts `/cucm phones-eol` and never replies, their entry lives forever (until process restart). If they later type any number — even in a different context — the bot interprets it as a phone model selection. This is verified at `app/cucm/phones_eol.py:335-346`: `handle_phone_lifecycle_selection()` fires for any digit-only message if a pending entry exists.

## Scope

**In scope:**
- Store a timestamp with each pending entry
- Check TTL in `handle_phone_lifecycle_selection()` — discard stale entries
- TTL: 5 minutes

**Out of scope:**
- Replacing in-memory state with a persistent store (Redis, DB)
- Supporting multiple simultaneous multi-step flows per user

## References

- State module: `app/state/pending_actions.py:24`
- Consumer: `app/cucm/phones_eol.py:202-210` (where pending is set), `app/cucm/phones_eol.py:329-356` (where it's consumed)

## Files expected to change

- `app/state/pending_actions.py` — document the expected dict shape with timestamp
- `app/cucm/phones_eol.py` — add timestamp when setting, check TTL when consuming

## Execution order

1. In `app/cucm/phones_eol.py:202`, when setting the pending entry, add a timestamp:
   ```python
   import time
   pending_actions[sender_email] = {
       "type": "phone_lifecycle_model_select",
       "models": models,
       "created_at": time.time(),
   }
   ```
2. In `handle_phone_lifecycle_selection()`, after retrieving `pending`, add TTL check:
   ```python
   TTL_SECONDS = 300  # 5 minutes
   if time.time() - pending.get("created_at", 0) > TTL_SECONDS:
       pending_actions.pop(sender_email, None)
       return None  # treat as no pending action
   ```
3. Update `app/state/pending_actions.py` docstring to document the expected shape including `created_at`
4. Manual verification

## Acceptance criteria

- [ ] A pending entry older than 5 minutes is discarded and treated as if it doesn't exist
- [ ] A fresh pending entry (within 5 minutes) still works correctly
- [ ] After TTL expiry, the user can start a new `/cucm phones-eol` flow cleanly

## Manual verification

1. Run `/cucm phones-eol` — see model list
2. Wait 6+ minutes (or temporarily set `TTL_SECONDS = 10` for testing)
3. Reply with `1` — expect either "Unknown command" or the command is re-routed, not a model detail
4. Run `/cucm phones-eol` again — fresh list appears

## Gotchas & learned lessons

- `time.time()` returns a float (epoch seconds). Simple subtraction gives elapsed seconds.
- After TTL expiry and discard, return `None` from `handle_phone_lifecycle_selection()` so the command router continues to the next handler. Don't return an error message — the expired entry is invisible to the user.
