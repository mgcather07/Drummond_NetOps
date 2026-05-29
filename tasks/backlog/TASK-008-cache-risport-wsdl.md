---
id: TASK-008
category: spec
phase: phase-2
status: backlog
---

# TASK-008: Cache RISPort WSDL locally

## User story

As a **bot user running `/cucm phone` or `/cucm trunk`**, I want the command to respond faster and not fail if CUCM is momentarily slow to serve the WSDL.

## Why this matters

`app/cucm/risport.py:27` and `app/cucm/trunk_status.py:27` both construct a Zeep client with:
```python
wsdl = f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70?wsdl"
```
Zeep fetches this WSDL from CUCM at client creation time — which happens inside every phone status and trunk status call. This adds a live network fetch to every lookup. The AXL client uses a local WSDL file (`schema/15.0/AXLAPI.wsdl`) — RISPort should too.

## Scope

**In scope:**
- Download the RISPort WSDL from CUCM once and save to `schema/15.0/RISService70.wsdl`
- Update `risport.py` and `trunk_status.py` to use the local file path
- Document that the WSDL may need to be re-downloaded after a CUCM upgrade

**Out of scope:**
- Caching the Zeep client object across requests (bigger refactor)
- Handling CUCM version upgrades automatically

## References

- RISPort client: `app/cucm/risport.py:26-36`
- Trunk status client: `app/cucm/trunk_status.py:26-36`
- AXL WSDL (local pattern to follow): `schema/15.0/AXLAPI.wsdl`

## Files expected to change

- `schema/15.0/RISService70.wsdl` — new file (downloaded from CUCM)
- `app/cucm/risport.py` — use local WSDL path
- `app/cucm/trunk_status.py` — use local WSDL path

## Execution order

1. Download the WSDL from your CUCM (requires VPN/network access to CUCM):
   ```sh
   curl -k -u $CUCM_USERNAME:$CUCM_PASSWORD \
     "https://$CUCM_HOST:8443/realtimeservice2/services/RISService70?wsdl" \
     -o schema/15.0/RISService70.wsdl
   ```
2. Confirm the file downloaded correctly (`head -5 schema/15.0/RISService70.wsdl` should show XML)
3. In `app/cucm/risport.py`, replace the WSDL URL with the local path:
   ```python
   # Before:
   wsdl = f"https://{CUCM_HOST}:8443/realtimeservice2/services/RISService70?wsdl"
   # After:
   wsdl = "schema/15.0/RISService70.wsdl"
   ```
4. Do the same in `app/cucm/trunk_status.py`
5. Test: `/cucm phone <MAC>` and `/cucm trunk <alias>` — confirm live status still returns
6. Add a note to `schema/15.0/` or `CLAUDE.md` that this WSDL must be re-downloaded after CUCM upgrades

## Acceptance criteria

- [ ] `schema/15.0/RISService70.wsdl` exists and is valid XML
- [ ] `/cucm phone <MAC>` returns live registration status using the local WSDL
- [ ] `/cucm trunk <alias>` returns live status using the local WSDL
- [ ] `app/cucm/risport.py` and `trunk_status.py` no longer reference the WSDL URL

## Manual verification

1. With network access to CUCM, run `/cucm phone <known-MAC>` — confirm registration status returned
2. Run `/cucm health` — confirm trunk status section still works
3. Check that the Zeep client doesn't make an extra network call to fetch WSDL (observable by disabling CUCM network temporarily)

## Gotchas & learned lessons

- The RISPort WSDL may import additional XSD files. If Zeep throws on parsing, check if the WSDL references relative imports that also need to be downloaded.
- After a CUCM upgrade, the WSDL may change. Add a note to `CLAUDE.md` under "Gated files" that `schema/15.0/RISService70.wsdl` should be refreshed after CUCM version upgrades.
