# Phases

High-level phase-only roadmap for this project. Each phase has a
**name**, a **scope paragraph** (2–4 sentences), and a status. The
ordered task list for each phase lives in [`ROADMAP.md`](ROADMAP.md).

---

## How to read this file

- 📋 **Queued** — defined, not started.
- 🚧 **Active** — current work happens here.
- ✅ **Shipped** — phase done; record the version that landed it.

---

## Phase 0 — Foundation (already shipped)

**Status:** ✅ Shipped — 2026-05-27

**Scope.** Get a working Webex bot that can receive messages, authenticate users, and execute core CUCM commands (phones, trunks, call flow, route plan, dial plan, health, phones-eol). Webhook handler, auth gate, and command router all wired end-to-end.

---

## Phase 1 — Security & Correctness

**Status:** 🚧 Active

**Scope.** Fix the four correctness issues identified in the wrangle audit before any feature work proceeds: wire the existing RBAC system into the command router, remove dead code that looks authoritative, kill always-on PII logging, and add Webex webhook signature validation. None of these require touching CUCM logic. Done when every authorized user is correctly gated by their role, the codebase has no misleading dead code, and the webhook endpoint validates Webex signatures.

---

## Phase 2 — Reliability

**Status:** 📋 Queued

**Scope.** Close the reliability gaps before the command surface grows: startup env validation, fix the webhook registration script, add a TTL to pending interactive state, cache the RISPort WSDL locally, and move blocking I/O off the async event loop. Done when the bot survives a process restart cleanly, gives clear errors for bad config, and doesn't block under concurrent requests.

---

## Phase 3 — Palo Alto & Feature Expansion

**Status:** 📋 Queued

**Scope.** Expand the bot beyond CUCM: add the first Palo Alto firewall commands (policy match, NAT lookup), improve Webex output with markdown formatting, and add more network commands (traceroute, show interface, show ip route). Done when at least one Palo Alto command returns accurate data from the live firewall and Webex messages use consistent markdown formatting across all handlers.

---

*(Add phases as the project evolves. Use `/plan` to think through new phases; use `/task` to file tasks under existing phases.)*
