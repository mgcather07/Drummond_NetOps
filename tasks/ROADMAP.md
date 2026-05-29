# Roadmap

Phase-by-phase task registry. For phase scope prose, see [`PHASES.md`](PHASES.md).

---

## Phase 1 — Security & Correctness

> Wire RBAC, remove dead code, kill PII logging, add webhook signature validation.

| ID | Title | Status |
|---|---|---|
| [TASK-001](backlog/TASK-001-wire-rbac.md) | Wire RBAC into command router | backlog |
| [TASK-002](backlog/TASK-002-delete-dead-auth-file.md) | Delete dead authorized_users.py | backlog |
| [TASK-003](backlog/TASK-003-remove-pii-logging.md) | Remove always-on PII debug logging | backlog |
| [TASK-004](backlog/TASK-004-webhook-signature-validation.md) | Add Webex webhook signature validation | backlog |

---

## Phase 2 — Reliability

> Startup validation, webhook upsert, PENDING_ACTIONS TTL, local RISPort WSDL, async fix.

| ID | Title | Status |
|---|---|---|
| [TASK-005](backlog/TASK-005-startup-env-validation.md) | Validate env vars at startup | backlog |
| [TASK-006](backlog/TASK-006-fix-create-webhook.md) | Fix create_webhook.py (upsert + env URL) | backlog |
| [TASK-007](backlog/TASK-007-pending-actions-ttl.md) | Add TTL to PENDING_ACTIONS | backlog |
| [TASK-008](backlog/TASK-008-cache-risport-wsdl.md) | Cache RISPort WSDL locally | backlog |
| [TASK-009](backlog/TASK-009-fix-async-blocking-io.md) | Move blocking I/O off async event loop | backlog |

---

## Phase 3 — Bot Cleanup & Quality

> Markdown formatting, complete help system, standardized errors, structured logging, command cleanup.

| ID | Title | Status |
|---|---|---|
| [TASK-011](backlog/TASK-011-webex-markdown-formatting.md) | Webex markdown formatting across all handlers | backlog |
| [TASK-013](backlog/TASK-013-help-system-overhaul.md) | Help system overhaul — complete and accurate | backlog |
| [TASK-014](backlog/TASK-014-standardized-error-handling.md) | Standardized error handling and response format | backlog |
| [TASK-015](backlog/TASK-015-structured-logging.md) | Replace print() with structured logging | backlog |
| [TASK-016](backlog/TASK-016-command-routing-cleanup.md) | Command routing cleanup, aliases, normalization | backlog |

---

## Phase 4 — Palo Alto Integration

> Full PAN-OS XML API: policy match, NAT, HA, interfaces, address search, routes.

| ID | Title | Status |
|---|---|---|
| [TASK-010](backlog/TASK-010-palo-alto-first-command.md) | Palo Alto policy match + NAT lookup | backlog |
| [TASK-017](backlog/TASK-017-palo-alto-health-ha.md) | Palo Alto HA status & system health | backlog |
| [TASK-018](backlog/TASK-018-palo-alto-interfaces-zones.md) | Palo Alto interface, zone & route info | backlog |
| [TASK-019](backlog/TASK-019-palo-alto-address-rule-search.md) | Palo Alto address/rule search by IP | backlog |

---

## Phase 5 — Network Device Full Integration

> Named device registry, ARP/MAC tables, CDP/LLDP, VLAN/port info, interface error stats.

| ID | Title | Status |
|---|---|---|
| [TASK-012](backlog/TASK-012-expand-network-commands.md) | Expand network commands (traceroute, show interface, show ip route) | backlog |
| [TASK-020](backlog/TASK-020-network-device-registry.md) | Named network device registry | backlog |
| [TASK-021](backlog/TASK-021-arp-mac-table-lookup.md) | ARP table + MAC address table lookup | backlog |
| [TASK-022](backlog/TASK-022-cdp-lldp-neighbors.md) | CDP/LLDP neighbor discovery | backlog |
| [TASK-023](backlog/TASK-023-vlan-port-membership.md) | VLAN info and port membership | backlog |
| [TASK-024](backlog/TASK-024-interface-error-stats.md) | Interface error and utilization stats | backlog |

---

## Phase 6 — vSphere Integration

> VM inventory/status, power operations, host/cluster health, datastore capacity, snapshots.

| ID | Title | Status |
|---|---|---|
| [TASK-025](backlog/TASK-025-vsphere-setup-vm-status.md) | vSphere setup + VM status and inventory | backlog |
| [TASK-026](backlog/TASK-026-vsphere-power-operations.md) | VM power state operations | backlog |
| [TASK-027](backlog/TASK-027-vsphere-host-cluster-datastore.md) | Host, cluster and datastore status | backlog |
| [TASK-028](backlog/TASK-028-vsphere-vm-network-info.md) | VM network info (vNIC, port group, VLAN) | backlog |
| [TASK-029](backlog/TASK-029-vsphere-snapshot-inventory.md) | Snapshot inventory and age report | backlog |
