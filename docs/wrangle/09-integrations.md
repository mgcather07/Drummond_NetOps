# External integrations

> **Read.** Five runtime integrations: Webex (inbound webhook + outbound API), CUCM AXL SOAP, CUCM RISPort SOAP, CUCM SSH CLI, and Cisco IOS SSH. No queuing, retries, or circuit breaking on any of them.

## What's actually here

### 1. Webex Teams

- **Inbound**: Webex POSTs to `POST /webhook` when a message is created in a room the bot is in. The payload only contains the message ID — the app must call `webex_api.messages.get(message_id)` to get the actual text.
- **Outbound**: `webex_api.messages.create(roomId=..., text=...)` sends replies. All replies are plain text — no cards, no markdown formatting.
- **Bot mention handling**: In group spaces, messages start with "Drummond" (the bot name). `command_router.py:22-23` strips this prefix. In 1:1 spaces, no prefix.
- **Webhook registration**: `create_webhook.py` — must be run manually when the URL changes. Currently has a hardcoded ngrok URL.

### 2. CUCM AXL SOAP API

- **Endpoint**: `https://{CUCM_HOST}:8443/axl/`
- **Auth**: HTTP Basic auth (`CUCM_USERNAME` / `CUCM_PASSWORD`)
- **Schema**: Loaded from `schema/15.0/AXLAPI.wsdl` on disk (local file, not fetched from CUCM)
- **Calls made**:
  - `getPhone(name)` — phone config
  - `getSipTrunk(name)` — trunk config
  - `getRoutePattern(pattern, routePartitionName)` — route pattern details
  - `getCss(name)` — calling search space partitions
  - `executeSQLQuery(sql)` — raw Informix SQL for dial plan, route plan, and phone inventory queries
- **SSL**: `verify=False` on all sessions; `urllib3` warnings suppressed globally

### 3. CUCM RISPort SOAP API

- **Endpoint**: `https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70`
- **WSDL**: Fetched live from CUCM on every call (no local copy)
- **Auth**: HTTP Basic auth (same credentials as AXL)
- **Calls made**: `selectCmDeviceExt(StateInfo, CmSelectionCriteria)` — live device registration/status
- **Used for**: Phone registration (`risport.py`), trunk status (`trunk_status.py`), health check

### 4. CUCM SSH CLI

- **Target**: `CUCM_HOST:22`
- **Auth**: `CUCM_SSH_USERNAME` / `CUCM_SSH_PASSWORD`
- **Device type**: `generic` (not `cisco_ios`)
- **Commands**: `utils dbreplication runtimestate`, then optionally a `file view activelog ...` follow-up
- **Wait**: Up to 120 seconds for the first command, 90 for the second
- **Parsing**: Regex on raw output looking for `g_\d+_...` node lines and specific status strings

### 5. Cisco IOS SSH (network devices)

- **Target**: User-supplied IP from `/show version <ip>` command
- **Auth**: `NETWORK_USERNAME` / `NETWORK_PASSWORD` (shared credential for all devices)
- **Device type**: `cisco_ios`
- **Commands**: `show version`
- **Output**: Truncated to 3,000 characters before sending to Webex

### 6. OS ping

- **Implementation**: `subprocess.run(["ping", "-c", "4", target])`
- **Target**: User-supplied string from `/ping <target>`
- **Timeout**: 10 seconds

## Open questions

- No retry logic on any integration. A transient CUCM AXL timeout returns an error to the user with no automatic retry.
- The Webex webhook has no secret set — no signature validation on inbound requests.
