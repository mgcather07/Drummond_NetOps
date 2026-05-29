# Dependencies & external services

> **For future task work.** When `/task` does external reconnaissance, this file is the starting list of doc URLs to fetch. Keep it current — re-run `/wrangle` after major dep changes.

**Audited at.** `e00fc16` on 2026-05-27
**Manifest sources read.** `requirements.txt`

## Libraries & frameworks

| Library | Version | Used for | Docs |
|---|---|---|---|
| `fastapi` | 0.128.8 | Web framework; route definitions, request/response models | https://fastapi.tiangolo.com/ |
| `uvicorn` | 0.39.0 | ASGI server; runs the FastAPI app | https://www.uvicorn.org/ |
| `pydantic` | 2.13.4 | FastAPI data validation; also used implicitly for request bodies | https://docs.pydantic.dev/ |
| `starlette` | 0.49.3 | FastAPI's underlying HTTP toolkit (transitive) | https://www.starlette.io/ |
| `webexteamssdk` | 1.7 | Webex Teams REST API client — send messages, fetch message details, create webhooks | https://webexteamssdk.readthedocs.io/ |
| `zeep` | 4.3.2 | SOAP client — CUCM AXL API and RISPort API | https://docs.python-zeep.org/ |
| `requests` | 2.32.5 | HTTP; used as the Zeep transport session and for CUCM node reachability checks | https://docs.python-requests.org/ |
| `netmiko` | 4.6.0 | SSH to network devices (Cisco IOS `show version`) and CUCM SSH CLI (`utils dbreplication`) | https://ktbyers.github.io/netmiko/ |
| `ntc_templates` | 8.1.0 | TextFSM templates for Netmiko — pulled in as netmiko dependency, not directly used in app code | https://github.com/networktocode/ntc-templates |
| `textfsm` | 2.1.0 | Netmiko dependency; template-based CLI output parsing | https://github.com/google/textfsm |
| `pyodbc` | 5.3.0 | SQL Server connection via ODBC Driver 18; used for `dbo.users` CRUD | https://github.com/mkleehammer/pyodbc/wiki |
| `python-dotenv` | 1.2.1 | Loads `.env` file into `os.environ` at startup | https://saurabh-kumar.com/python-dotenv/ |
| `PyJWT` | 1.7.1 | JWT — imported in requirements but not visibly used in app source. Possibly a future auth token mechanism. | https://pyjwt.readthedocs.io/ |
| `bcrypt` | 5.0.0 | Password hashing — in requirements but not visibly used in app source | https://pypi.org/project/bcrypt/ |
| `cryptography` | 48.0.0 | Paramiko/Netmiko SSH dependency | https://cryptography.io/ |
| `paramiko` | 5.0.0 | SSH — Netmiko dependency | https://www.paramiko.org/ |
| `lxml` | 6.1.0 | Zeep XML parsing dependency | https://lxml.de/ |
| `isodate` | 0.7.2 | Zeep SOAP date parsing dependency | https://pypi.org/project/isodate/ |
| `pytz` | 2026.2 | Timezone handling (transitive) | https://pythonhosted.org/pytz/ |

## Third-party services & APIs

| Service | Used for | Docs |
|---|---|---|
| Webex Teams (Cisco) | Inbound webhook delivery + outbound message API | https://developer.webex.com/docs/api/v1/messages |
| CUCM AXL SOAP API | Phone/trunk/route plan/dial plan queries | https://developer.cisco.com/site/axl/ |
| CUCM RISPort SOAP API | Live device registration status (phones, trunks) | https://developer.cisco.com/docs/sxml/#!risport70-api-reference |
| CUCM SSH CLI | Database replication status via `utils dbreplication runtimestate` | CUCM admin CLI (no public doc URL) |
| SQL Server (Microsoft) | User store (`dbo.users`) | https://docs.microsoft.com/en-us/sql/odbc/ |

## Dev / build / CI dependencies

| Tool | Version | Purpose | Docs |
|---|---|---|---|
| Python | 3.9 | Runtime | https://docs.python.org/3.9/ |
| ODBC Driver 18 | system | SQL Server connectivity — must be installed on host OS separately | https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server |
| pip | (system) | Package management | https://pip.pypa.io/ |
| ngrok | (external) | Local dev tunnel for Webex webhook delivery | https://ngrok.com/docs |

## Notes

- `PyJWT 1.7.1` is old (1.x API, not 2.x). If JWT is used in the future, the API changed significantly in 2.0. Worth upgrading before use.
- `bcrypt` is in requirements but unused in app source — likely a vestige.
- `webexteamssdk 1.7` is the last published version of this SDK (Cisco has not updated it). The underlying REST API still works but the SDK is effectively unmaintained.
- All CUCM HTTPS connections use `verify=False` — no TLS validation against CUCM's self-signed cert. Acceptable for internal lab; document if this changes.
