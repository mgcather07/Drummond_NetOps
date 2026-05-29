# Phases

High-level phase-only roadmap for this project. Each phase has a
**name**, a **scope paragraph**, and a status. The ordered task list
for each phase lives in [`ROADMAP.md`](ROADMAP.md).

---

## How to read this file

- 📋 **Queued** — defined, not started.
- 🚧 **Active** — current work happens here.
- ✅ **Shipped** — phase done; record the version that landed it.

---

## Phase 0 — Foundation

**Status:** ✅ Shipped — 2026-05-27

**Scope.** Working Webex bot with auth gate, CUCM commands (phones,
trunks, call flow, route plan, dial plan, health, phones-eol), and
webhook handler end-to-end.

---

## Phase 1 — Security & Correctness

**Status:** 🚧 Active

**Scope.** Fix four correctness issues before any feature work:
wire the RBAC system into the command router, delete dead code,
kill always-on PII logging, and add Webex webhook signature validation.
Done when every user is correctly gated by role and the webhook
validates signatures.

---

## Phase 2 — Reliability

**Status:** 📋 Queued

**Scope.** Close reliability gaps before the command surface grows:
startup env validation, fix webhook registration script, PENDING_ACTIONS
TTL, cache RISPort WSDL locally, and move blocking I/O off the async
event loop. Done when the bot survives restarts cleanly and gives clear
errors for bad config.

---

## Phase 3 — Bot Cleanup & Quality

**Status:** 📋 Queued

**Scope.** Make the bot production-quality: overhaul the help system
so it's complete and accurate, standardize error handling and response
format across all handlers, replace all `print()` statements with
structured logging, apply markdown formatting, and clean up command
routing (aliases, normalization, dead paths). Done when every command
has consistent formatting, comprehensive help text, and errors are
logged — not printed — to stdout.

---

## Phase 4 — Palo Alto Integration

**Status:** 📋 Queued

**Scope.** Full PAN-OS XML API integration: policy match, NAT lookup,
HA status, interface and zone info, address/rule search by IP, and
route table lookup. Done when the team can answer any common firewall
question from Webex without logging into the Palo Alto GUI.

---

## Phase 5 — Network Device Full Integration

**Status:** 📋 Queued

**Scope.** Expand SSH-based network device access beyond ping and
show version: build a named device registry so users say `/net
CORE-SW1 ...` instead of raw IPs, add ARP table, MAC address table,
CDP/LLDP neighbors, VLAN/port membership, and interface error stats.
Done when the team can diagnose most Layer 2/3 issues from Webex.

---

## Phase 6 — vSphere Integration

**Status:** 📋 Queued

**Scope.** pyVmomi-based vCenter integration: VM inventory and status,
controlled power state operations (view + limited actions gated to
master role), host and cluster health, datastore capacity, and snapshot
age reporting. Done when the team can answer "what's the state of VM X"
and get a datastore capacity summary without opening vSphere Client.
