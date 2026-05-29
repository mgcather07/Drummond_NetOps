# Open questions

Things that couldn't be verified from reading the code alone.

- **`dbo.users` table origin** — No `CREATE TABLE` script or migration exists in the repo. How was the table created? Is there a manual SQL script somewhere?

- **`app/data/authorized_users.py` purpose** — Defines `AUTHORIZED_USERS` with real email addresses and `ROLE_PERMISSIONS`. Nothing imports it. Is this the previous auth mechanism, predating the SQL-backed system? If so, it should be deleted to avoid confusion.

- **`PyJWT` and `bcrypt` usage** — Both are in `requirements.txt` but not visibly used in any app source file. Are they used by a dependency, or were they added for a planned feature?

- **SQL Server location** — Is the SQL Server running on-prem on the same network as CUCM? Is it the CUCM Informix DB exposed via an ODBC bridge, or a separate SQL Server instance?

- **CUCM subscriber reachability** — The Bogota, Laloma, and Santa Marta subscribers use `192.168.x.x` addresses. Is the bot expected to reach these over VPN or MPLS? Are they reachable from wherever the bot will be hosted?

- **`test_sql.py`** — Not read during this audit. Is it a one-shot dev script or does it contain anything worth keeping?

- **Permanent hosting** — Where will the bot run in production? The deploy target affects webhook URL management, SSL termination, and whether Windows auth is feasible for SQL Server.

- **`app/palo/`** — Empty stub. Is Palo Alto integration planned? What queries are needed (policy lookup, NAT, security zones)?

- **`app/utils/`** — Empty. What utilities are planned for extraction?

- **Multi-site CUCM routing** — The `app/data/sites.py` has sites with `gateway: "LPUC"` vs `gateway: "Jasper"`. Does the call flow logic need to account for which gateway a site uses, or is this field informational only?
