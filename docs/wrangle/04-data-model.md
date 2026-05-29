# Data model

> **Read.** The project has one owned database table (`dbo.users`) and queries two external systems (CUCM and SQL Server) — no ORM, no migrations, no schema file. Static reference data lives in Python dicts.

## What's actually here

### Owned data — SQL Server `dbo.users`

The only table this app owns and writes to. Inferred schema from `app/security/auth.py:67-73` and `app/admin/users.py:87-96`:

| Column | Type | Notes |
|---|---|---|
| `email` | varchar | Lowercase; primary lookup key |
| `name` | varchar | Display name |
| `role_name` | varchar | One of: `master`, `admin`, `user` |
| `enabled` | bit | 0 = disabled, 1 = enabled |

No primary key or index is visible from app code. No migration history. The table must exist before the app can boot (first auth check will fail with a SQL error if it doesn't).

### Queried external data — CUCM

All CUCM data is read-only from the app's perspective:

- **Phones** — `getPhone(name)` AXL call → device pool, CSS, location, lines (pattern + partition)
- **SIP trunks** — `getSipTrunk(name)` AXL call → destinations, security/SIP profiles
- **Live device status** — RISPort `selectCmDeviceExt` → registration status, IP, firmware, active node
- **Dial plan** — `executeSQLQuery` on `numplan`, `typepatternusage`, `routepartition` tables
- **Route pattern details** — `getRoutePattern(pattern, partition)` → gateway, digit manipulation
- **CSS partitions** — `getCss(name)` → member partition list
- **DB replication** — SSH to CUCM publisher → `utils dbreplication runtimestate` CLI output, parsed by regex

### Static reference data — Python dicts

Checked into source; no DB backing:

| File | What it holds |
|---|---|
| `app/data/sites.py` | 12 named sites with aliases, addresses, gateway, default CSS |
| `app/data/trunks.py` | 2 SIP trunk definitions with CUCM names and aliases |
| `app/data/did_blocks.py` | DID ranges per site (NPA/NXX + low/high subscriber) |
| `app/data/cucm_nodes.py` | 5 CUCM nodes with IPs, hostnames, replication state IDs |
| `app/data/model_lookup.py` | CUCM model enum → display name (~30 mappings) |
| `app/data/phone_eol_catalog.py` | ~25 Cisco phone models with EOL status, dates, replacement |

## How it fits

The static data in `app/data/` acts as configuration. Changes to trunk names, site DID blocks, or CUCM node IPs require a code edit and redeploy. There is no admin UI or database table for these — they are intentionally hardcoded.

## Open questions

- No `CREATE TABLE` script or migration exists for `dbo.users`. How was the table created?
- `app/data/authorized_users.py` defines a static user dict that is never imported anywhere — dead code?
