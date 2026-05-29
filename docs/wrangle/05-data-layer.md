# Data layer

> **Read.** Five distinct data access mechanisms are used: Zeep SOAP (AXL), Zeep SOAP (RISPort), Netmiko SSH (CUCM CLI), Netmiko SSH (Cisco IOS), pyodbc (SQL Server). Every connection is opened and closed per-request with no pooling.

## What's actually here

### 1. CUCM AXL (Zeep SOAP)

Used by: `app/cucm/phones.py`, `trunks.py`, `dial_plan.py`, `route_plan.py`, `route_plan_lookup.py`, `route_pattern_details.py`, `css.py`, `phones_eol.py`, `free_extensions.py`

Pattern in every file:
```python
session = requests.Session()
session.verify = False  # SSL disabled
session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)
transport = Transport(session=session, timeout=N)
client = Client(wsdl="schema/15.0/AXLAPI.wsdl", transport=transport)
service = client.create_service("{http://www.cisco.com/AXLAPIService/}AXLAPIBinding", axl_url)
```
Each handler rebuilds this stack from scratch per call. No shared Zeep client.

Two query styles are used:
- **Native AXL methods**: `service.getPhone()`, `service.getSipTrunk()`, `service.getRoutePattern()`, `service.getCss()` — structured SOAP calls using the WSDL types
- **`executeSQLQuery`**: Raw Informix SQL via AXL against the CUCM internal DB — used for dial plan matching (`numplan` + `typepatternusage` + `routepartition` joins), route plan lookup, and full phone inventory for EOL reporting

### 2. CUCM RISPort (Zeep SOAP)

Used by: `app/cucm/risport.py`, `app/cucm/trunk_status.py`

Different WSDL endpoint, fetched at runtime from CUCM:
```python
wsdl = f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70?wsdl"
```
Calls `service.selectCmDeviceExt()` with `CmSelectionCriteria`. Returns live registration status, IP, firmware, active node. No schema file on disk — WSDL is fetched from the live CUCM server on each call.

### 3. CUCM SSH (Netmiko — generic device type)

Used by: `app/cucm/dbreplication.py`

```python
device = {"device_type": "generic", "host": CUCM_HOST, ...}
connection = ConnectHandler(**device)
connection.write_channel("utils dbreplication runtimestate\n")
```
Parses the CLI output with regex to extract replication node state. Waits up to 120 seconds for the prompt (CUCM DB replication command is slow). Optionally runs a `file view activelog ...` follow-up command.

### 4. Network device SSH (Netmiko — cisco_ios)

Used by: `app/network/show_version.py`

Standard Cisco IOS connection with specific KEX algorithms disabled (for compatibility with older devices):
```python
device = {"device_type": "cisco_ios", "host": host, ...}
connection.send_command("show version")
```
Output truncated to 3000 chars before sending to Webex.

### 5. SQL Server (pyodbc)

Used by: `app/database/sql.py`, called by `app/security/auth.py` and `app/admin/users.py`

```python
conn = pyodbc.connect(connection_string)  # new connection per call
cursor = conn.cursor()
cursor.execute(sql, params)
conn.close()
```
Supports two auth modes (`SQL_AUTH_MODE` env var): SQL auth (username/password) or Windows integrated auth (`Trusted_Connection=yes`). Windows auth path is not tested on macOS. No connection pool — every SQL call opens and closes a fresh connection.

### 6. OS subprocess (ping)

Used by: `app/network/ping.py`

```python
subprocess.run(["ping", "-c", "4", target], capture_output=True, timeout=10)
```
No input sanitization on `target` before passing to subprocess. See `12-smells-and-risks.md`.

## How it fits

Every data connection is ephemeral and synchronous. The webhook handler is `async def` but makes no `await` calls — all I/O (SQL, SOAP, SSH) is blocking. Under concurrent load, uvicorn workers will queue behind slow I/O (CUCM SSH can take 120 seconds).
