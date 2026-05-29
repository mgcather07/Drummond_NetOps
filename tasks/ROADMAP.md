# Roadmap

Phase-by-phase task registry for this project. Each phase has a name,
a scope paragraph, and an ordered list of tasks. Order implies
suggested ship order.

For phase scopes only (no task lists), see [`PHASES.md`](PHASES.md).

---

## Phase 1 — Security & Correctness

> **Scope.** Fix the four correctness issues identified in the wrangle audit before any feature work proceeds: wire the existing RBAC system into the command router, remove dead code that looks authoritative, kill always-on PII logging, and add Webex webhook signature validation.

Tasks (in suggested ship order):

- [TASK-001](backlog/TASK-001-wire-rbac.md) — Wire RBAC into command router
- [TASK-002](backlog/TASK-002-delete-dead-auth-file.md) — Delete dead authorized_users.py
- [TASK-003](backlog/TASK-003-remove-pii-logging.md) — Remove always-on PII debug logging
- [TASK-004](backlog/TASK-004-webhook-signature-validation.md) — Add Webex webhook signature validation

---

## Phase 2 — Reliability

> **Scope.** Close the reliability gaps before the command surface grows: startup env validation, fix the webhook registration script, add a TTL to pending interactive state, cache the RISPort WSDL locally, and move blocking I/O off the async event loop.

Tasks (in suggested ship order):

- [TASK-005](backlog/TASK-005-startup-env-validation.md) — Validate env vars at startup
- [TASK-006](backlog/TASK-006-fix-create-webhook.md) — Fix create_webhook.py (upsert + env URL)
- [TASK-007](backlog/TASK-007-pending-actions-ttl.md) — Add TTL to PENDING_ACTIONS
- [TASK-008](backlog/TASK-008-cache-risport-wsdl.md) — Cache RISPort WSDL locally
- [TASK-009](backlog/TASK-009-fix-async-blocking-io.md) — Move blocking I/O off async event loop

---

## Phase 3 — Palo Alto & Feature Expansion

> **Scope.** Expand the bot beyond CUCM: add the first Palo Alto firewall commands, improve Webex output with markdown formatting, and add more network commands.

Tasks (in suggested ship order):

- [TASK-010](backlog/TASK-010-palo-alto-first-command.md) — Palo Alto first commands (policy + NAT)
- [TASK-011](backlog/TASK-011-webex-markdown-formatting.md) — Webex markdown formatting across all handlers
- [TASK-012](backlog/TASK-012-expand-network-commands.md) — Expand network commands (traceroute, show interface)
