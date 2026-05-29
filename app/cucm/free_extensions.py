from app.cucm.did_utils import expand_did_ranges
from app.cucm.route_plan import get_used_route_plan_patterns, is_did_used
from app.data.sites import get_site


def get_free_extension(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: /cucm free-extension <site>"

    site = get_site(parts[2])

    if not site:
        return f"❌ Unknown site: {parts[2]}\n\nTry /sites to view configured sites."

    site_key = site["key"]
    site_name = site["name"]

    dids = expand_did_ranges(site_key)

    if not dids:
        return f"❌ No DID blocks configured for site: {site_name} ({site_key})"

    try:
        used_patterns = get_used_route_plan_patterns()

        available_dids = [
            did for did in dids
            if not is_did_used(did, used_patterns)
        ]

        if not available_dids:
            return f"""📞 Free Extension Lookup: {site_name}

No available extensions/DIDs found.

DID Blocks Scanned: {len(dids)}
Used Route Plan Patterns Checked: {len(used_patterns)}

❌ All configured DIDs appear to be used in CUCM.
"""

        first_available = available_dids[0]

        return f"""📞 Free Extension Lookup: {site_name} ({site_key})

Suggested Extension:
{first_available[-4:]}

Full DID:
{first_available}

Status:
✅ Available

DID Blocks Scanned:
{len(dids)}

Available DIDs Found:
{len(available_dids)}

CUCM Route Plan Patterns Checked:
{len(used_patterns)}

✅ Validated against CUCM route plan.
"""

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Free extension lookup failed for site %s", site_key)
        return error(translate_exception(e), hint="Check the site name and that CUCM is reachable.")