from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import os
import re
import requests
from typing import Optional

from app.data.sites import get_site
from app.cucm.css import get_css_partitions

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def cucm_pattern_to_regex(pattern: str) -> str:
    if not pattern:
        return ""

    regex = pattern
    regex = regex.replace(".", "")
    regex = regex.replace("X", r"\d")

    return f"^{regex}$"


def get_site_context(parts: list) -> Optional[str]:
    if "from" in parts:
        site_index = parts.index("from") + 1
        if site_index < len(parts):
            return parts[site_index]

    if "site" in parts:
        site_index = parts.index("site") + 1
        if site_index < len(parts):
            return parts[site_index]

    return None


def format_match(
    match_number: int,
    pattern: str,
    pattern_type: str,
    partition: str,
    description: str
) -> str:
    return f"""{match_number}. {pattern}
   Type: {pattern_type}
   Partition: {partition}
   Description: {description}"""


def classify_call_disposition(matches: list) -> str:
    if not matches:
        return """Final Call Disposition: ❌ Unroutable
Reason: No matching route patterns found."""

    likely_match = matches[-1].lower()

    if "block" in likely_match or "blocked" in likely_match or "filter" in likely_match:
        return """Final Call Disposition: 🚫 Possibly Blocked
Reason: The likely match appears to be a block/filter pattern."""

    if "type: route" in likely_match:
        return """Final Call Disposition: ✅ Routable
Reason: The likely selected match is a route pattern."""

    if "type: translation" in likely_match:
        return """Final Call Disposition: 🔄 Translation Pattern Matched
Reason: Additional routing may occur after translation."""

    return """Final Call Disposition: ⚠️ Review Required
Reason: A match was found, but the result could not be confidently classified."""


def get_dial_plan_match(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: /cucm route <dialed number>"

    dialed_number = re.sub(r"\D", "", parts[2])

    if not dialed_number:
        return "Usage: /cucm route <dialed number>"

    site_input = get_site_context(parts)
    site = get_site(site_input) if site_input else None

    allowed_partitions = None
    site_name = "Global Route Plan"
    css_name = "N/A"

    if site:
        site_name = f"{site['name']} ({site['key']})"
        css_name = site.get("default_css") or "N/A"

        if css_name != "N/A":
            allowed_partitions = get_css_partitions(css_name)

    try:
        axl_url = f"https://{CUCM_HOST}:8443/axl/"

        session = requests.Session()
        session.verify = False
        session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

        transport = Transport(session=session, timeout=30)

        client = Client(
            wsdl="schema/15.0/AXLAPI.wsdl",
            transport=transport
        )

        service = client.create_service(
            "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
            axl_url
        )

        sql = """
        SELECT
            n.dnorpattern,
            n.description,
            tk.name AS pattern_type,
            rp.name AS partition_name
        FROM numplan n
        LEFT JOIN typepatternusage tk
            ON n.tkpatternusage = tk.enum
        LEFT JOIN routepartition rp
            ON n.fkroutepartition = rp.pkid
        WHERE tk.name IN ('Route', 'Translation')
        """

        response = service.executeSQLQuery(sql=sql)
        data = serialize_object(response)

        result = data.get("return")

        if not result:
            return f"""📞 Dial Plan Analysis: {dialed_number}

Site Context: {site_name}
CSS: {css_name}

❌ No route patterns found in CUCM."""

        rows = result.get("row", [])

        if not isinstance(rows, list):
            rows = [rows]

        matches = []

        for row in rows:
            if not isinstance(row, list):
                row = [row]

            row_data = {}

            for column in row:
                if hasattr(column, "tag"):
                    row_data[column.tag] = column.text or ""

            pattern = row_data.get("dnorpattern", "")
            pattern_type = row_data.get("pattern_type", "Unknown")
            partition = row_data.get("partition_name", "None")
            description = row_data.get("description", "N/A")

            if allowed_partitions is not None and partition not in allowed_partitions:
                continue

            try:
                regex = cucm_pattern_to_regex(pattern)

                if regex and re.match(regex, dialed_number):
                    matches.append(
                        format_match(
                            match_number=len(matches) + 1,
                            pattern=pattern,
                            pattern_type=pattern_type,
                            partition=partition,
                            description=description,
                        )
                    )

            except Exception:
                continue

        if not matches:
            return f"""📞 Dial Plan Analysis: {dialed_number}

Site Context: {site_name}
CSS: {css_name}

Final Call Disposition: ❌ Unroutable
Reason: No matching route patterns found.

⚠️ Dialed number may fail routing."""

        matches_text = "\n\n".join(matches[:10])

        extra_note = ""
        if len(matches) > 10:
            extra_note = f"\n\nShowing first 10 of {len(matches)} matches."

        likely_match = matches[-1]
        disposition = classify_call_disposition(matches)

        return f"""📞 Dial Plan Analysis: {dialed_number}

Site Context: {site_name}
CSS: {css_name}

{disposition}

Possible Route Matches Found: {len(matches)}

Likely Selected Route:
{likely_match}

All Matches:
{matches_text}{extra_note}

✅ CUCM dial plan analysis completed."""

    except Exception as e:
        return f"""❌ Dial plan analysis failed.

Dialed Number: {dialed_number}
Site Context: {site_input or "Global Route Plan"}

Error Type: {type(e).__name__}
Error: {str(e)}"""


def extract_likely_route_from_text(dial_plan_result: str) -> dict:
    lines = dial_plan_result.splitlines()

    in_likely_section = False
    pattern = None
    partition = None

    for line in lines:
        clean = line.strip()

        if clean.startswith("Likely Selected Route"):
            in_likely_section = True
            continue

        if in_likely_section and clean.startswith("All Matches"):
            break

        if in_likely_section:
            # Handles: 3. 9.1[2-9]XX[2-9]XXXXXX
            if re.match(r"^\d+\.\s+", clean):
                pattern = re.sub(r"^\d+\.\s+", "", clean).strip()

            if clean.startswith("Partition:"):
                partition = clean.replace("Partition:", "").strip()

    return {
        "pattern": pattern,
        "partition": partition,
        "found": bool(pattern and partition),
    }