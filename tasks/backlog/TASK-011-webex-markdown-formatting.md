---
id: TASK-011
category: spec
phase: phase-3
status: backlog
---

# TASK-011: Webex markdown formatting across all handlers

## User story

As a **bot user**, I want command responses to use consistent markdown formatting (bold headers, code blocks, dividers) so that output is easier to read at a glance in the Webex client.

## Why this matters

Every handler currently returns a plain-text string. Webex supports a subset of markdown in messages: `**bold**`, ` ```code``` `, `---`, `> blockquote`. The current phone lookup output, for example, is a wall of text. Light formatting — bold field labels, code blocks for patterns and IPs — would significantly improve readability with minimal effort. All replies use `webex_api.messages.create(roomId=..., text=...)` which supports markdown.

## Scope

**In scope:**
- Standardize a formatting convention for all existing handlers
- Apply markdown to the most-used commands: `/cucm phone`, `/cucm trunk`, `/cucm health`, `/cucm phones-eol summary`, `/cucm call-flow`
- Define a shared formatting helper or template pattern in `app/utils/`

**Out of scope:**
- Webex Adaptive Cards (more complex, separate task)
- Changing command logic or data fetching
- Reformatting the raw ping/show-version output (keep as code block)

## References

- Webex markdown support: https://help.webex.com/en-us/article/nswnfbl/
- All handler files under `app/cucm/`, `app/network/`
- `app/utils/` — currently empty; this is the first thing that goes there

## Files expected to change

- `app/utils/formatting.py` — new: shared formatting helpers
- `app/cucm/phones.py` — apply formatting
- `app/cucm/trunks.py` — apply formatting
- `app/cucm/health.py` — apply formatting
- `app/cucm/phones_eol.py` — apply formatting to summary
- `app/cucm/call_flow.py` — apply formatting
- `app/network/ping.py` — wrap output in code block
- `app/network/show_version.py` — wrap output in code block

## Execution order

1. Create `app/utils/__init__.py` (empty)
2. Create `app/utils/formatting.py` with shared helpers:
   ```python
   def bold(text): return f"**{text}**"
   def code(text): return f"```\n{text}\n```"
   def section(title): return f"\n**{title}**"
   def divider(): return "\n---"
   ```
3. Apply to `app/cucm/phones.py` — bold field names (`**Description:**`), code block for lines
4. Apply to `app/cucm/trunks.py` — bold field names, code block for destinations
5. Apply to `app/cucm/health.py` — bold section headers, keep status icons
6. Apply to `app/cucm/phones_eol.py` — bold category headers
7. Apply to `app/cucm/call_flow.py` — bold section headers
8. Apply to `app/network/ping.py` and `show_version.py` — wrap raw output in code block
9. Send each reformatted command in Webex — verify rendering

## Acceptance criteria

- [ ] `/cucm phone <MAC>` response uses bold field labels
- [ ] `/cucm health` response uses bold section headers
- [ ] `/ping` output appears in a code block
- [ ] No formatting changes affect the data content — only presentation
- [ ] All handlers import from `app/utils/formatting.py` (no inline `**` sprinkled throughout)

## Manual verification

Send each command in Webex and visually confirm:
1. `/cucm phone <MAC>` — field labels are bold, lines section is readable
2. `/cucm trunk <alias>` — destinations readable, status icons visible
3. `/cucm health` — sections clearly separated, node list readable
4. `/ping 8.8.8.8` — output in code block

## Gotchas & learned lessons

- Webex markdown rendering varies slightly between desktop, mobile, and web clients. Test on the client your team actually uses.
- Keep emoji — they're used as status indicators (`✅`, `❌`, `⚠️`) and are load-bearing for quick scanning.
- Don't over-format. Bold headers + code blocks for machine output is enough. Avoid nested lists.
