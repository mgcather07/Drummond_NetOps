# Database / cloud infrastructure

> **Read.** The app depends on four external systems at runtime: SQL Server (user store), CUCM (AXL + RISPort + SSH), Webex cloud (message delivery), and the host OS for ping. No cloud hosting is configured yet.

## What's actually here

### SQL Server

- Hosts the `dbo.users` table — the only data the app owns and writes to
- Auth mode is configurable: SQL auth or Windows integrated auth (`SQL_AUTH_MODE` env var)
- Driver: ODBC Driver 18 for SQL Server must be installed on the host OS
- Connection string targets `SQL_SERVER` host with `Encrypt=no; TrustServerCertificate=yes` — no TLS validation

### CUCM (Cisco Unified Communications Manager)

Three separate interfaces consumed:

| Interface | Port | Protocol | Used for |
|---|---|---|---|
| AXL SOAP API | 8443 | HTTPS (TLS, verify=False) | Phone/trunk/route plan queries |
| RISPort SOAP API | 8443 | HTTPS (TLS, verify=False) | Live device registration status |
| SSH CLI | 22 | SSH | DB replication state |

The CUCM cluster has 5 nodes (from `app/data/cucm_nodes.py`):
- LPUC Publisher: `twr02smcm01` / `10.0.10.200`
- LPUC Subscriber: `twr04smcm03` / `10.10.200.200`
- Jasper Subscriber: `js3cmsub01` / `192.168.200.230`
- Bogota Subscriber: `BOGVIPCM03` / `192.168.170.234`
- Laloma Subscriber: `lalvipcm03` / `192.168.188.205`
- Santa Marta Subscriber: `stmvipcm03` / `192.168.197.230`

All AXL/RISPort calls target `CUCM_HOST` (the publisher). SSH for replication also targets `CUCM_HOST`.

### Webex cloud

The app receives events via an inbound HTTPS webhook (Webex POSTs to the app). It sends replies via the Webex REST API using the bot token. No persistent connection — stateless per-message.

### Network devices

SSH targets are arbitrary host IPs passed by the user in the `/show version` command. Credentials are shared: `NETWORK_USERNAME` / `NETWORK_PASSWORD` from env. No inventory — any IP is attempted.

### Hosting

Not yet configured. Development uses `ngrok` for a public URL (`create_webhook.py:17` has a hardcoded ngrok URL). No production host, no cloud stamp, no CI/CD.

## Open questions

- Where does the SQL Server actually run? On-prem? Same host as CUCM?
- Are the 192.168.x.x CUCM subscriber nodes reachable from the bot's deployment host?
