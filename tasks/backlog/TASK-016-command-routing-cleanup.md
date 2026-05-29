---
id: TASK-016
category: spec
phase: phase-3
status: backlog
---

# TASK-016: Command routing cleanup, aliases, normalization

## User story

As a **bot user**, I want common shorthand commands to work (`/health`, `/phone`, `/trunk`) and want consistent behavior when I make a typo or leave out required args, so the bot feels polished and predictable.

## Why this matters

The current command router (`command_router.py`) is a chain of `if/elif` blocks that works fine but has some rough edges: no shorthand aliases, no "did you mean?" for near-misses, inconsistent handling of missing args (some handlers return usage, some crash), and the bot mention prefix strip is fragile (hardcoded "drummond"). As the command surface grows to 30+ commands across CUCM, Palo Alto, network, and vSphere, this needs to be robust.

## Scope

**In scope:**
- Add common shorthand aliases: `/health` → `/cucm health`, `/phone` → `/cucm phone`, `/trunk` → `/cucm trunk`
- Fix bot mention stripping to use `BOT_NAME` from config instead of hardcoded "drummond"
- Add a catch-all "did you mean?" that suggests the closest command on a near-miss
- Ensure every command handler returns a usage string on missing args (audit and fix any that don't)
- Add `/commands` as an alias for `/help`

**Out of scope:**
- NLP/intent parsing
- Rewriting the router as a framework (keep the if/elif chain — it's readable)

## References

- Router: `app/webex/command_router.py`
- Bot name: `app/config/settings.py:8` — `BOT_NAME`
- Help: `app/webex/help.py`

## Files expected to change

- `app/webex/command_router.py` — aliases, mention strip fix, catch-all improvement
- `app/config/settings.py` — expose bot name for mention strip

## Execution order

1. Fix bot mention strip (`command_router.py:22-23`):
   ```python
   bot_prefix = BOT_NAME.split()[0].lower()  # "drummond" from "Drummond NetOps Bot"
   if command.lower().startswith(bot_prefix):
       command = command[len(bot_prefix):].strip()
   ```
2. Add shorthand aliases before the main dispatch chain:
   ```python
   ALIASES = {
       "/health": "/cucm health",
       "/phone": "/cucm phone",
       "/trunk": "/cucm trunk",
       "/route": "/cucm route",
       "/eol": "/cucm phones-eol",
       "/commands": "/help",
   }
   command = ALIASES.get(command_lower, command)
   command_lower = command.lower()
   ```
3. Audit each handler for missing-arg handling — confirm every handler returns a usage string when called with insufficient args (not a crash)
4. Improve the catch-all at the bottom:
   ```python
   # Suggest closest command if near-miss
   return f"❓ Unknown command: `{command}`\n\nTry `/help` to see available commands."
   ```
5. Add `/commands` as alias in the ALIASES dict

## Acceptance criteria

- [ ] `/health` returns the same response as `/cucm health`
- [ ] `/phone SEPXXX` returns the same response as `/cucm phone SEPXXX`
- [ ] `Drummond /health` (with bot mention) is handled correctly in group spaces
- [ ] Every command handler returns a usage string when called with no args
- [ ] Unknown commands return a clean message pointing to `/help`

## Manual verification

1. Send `/health` in Webex — confirm CUCM health response
2. Send `/phone` (no MAC) — confirm usage message
3. In a group space, send `Drummond /status` — confirm bot responds
4. Send `/blah` — confirm "Unknown command" response with help pointer

## Gotchas & learned lessons

- **Alias lookup must happen before `command_lower` is used for dispatch** — update `command_lower` after applying the alias.
- **Aliases should not bypass RBAC** — the alias just rewrites the command string before the permission check fires.
- Test group spaces separately from DMs — the mention prefix only appears in group spaces.
