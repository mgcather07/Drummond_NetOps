from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import os
import re
import requests

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


def normalize_pattern(value: str) -> str:
    if not value:
        return ""

    return re.sub(r"\D", "", str(value))


def get_route_plan(command: str) -> str:
    parts = command.split()

    if len(parts) < 3:
        return "Usage: /cucm route-plan <pattern>"

    search_value = parts[2].strip()
    normalized_search = normalize_pattern(search_value)

    if not normalized_search:
        return "Usage: /cucm route-plan <pattern>"

    last_4 = normalized_search[-4:]
    last_7 = normalized_search[-7:] if len(normalized_search) >= 7 else normalized_search
    last_10 = normalized_search[-10:] if len(normalized_search) >= 10 else normalized_search

    search_terms = list({
        search_value,
        normalized_search,
        last_10,
        last_7,
        last_4,
    })

    where_clause = " OR ".join([
        f"n.dnorpattern LIKE '%{term}%'"
        for term in search_terms
        if term
    ])

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

        sql = f"""
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
        WHERE {where_clause}
        ORDER BY n.dnorpattern
        """

        response = service.executeSQLQuery(sql=sql)
        data = serialize_object(response)

        result = data.get("return")

        if not result:
            return f"""🔎 CUCM Route Plan Lookup: {search_value}

No route plan matches found.

✅ Pattern appears unused in CUCM route plan."""

        rows = result.get("row", [])

        if not rows:
            return f"""🔎 CUCM Route Plan Lookup: {search_value}

No route plan matches found.

✅ Pattern appears unused in CUCM route plan."""

        if not isinstance(rows, list):
            rows = [rows]

        matches = []

        for row in rows:
            if not isinstance(row, list):
                row = [row]

            row_data = {}

            for column in row:
                if hasattr(column, "tag"):
                    row_data[column.tag] = column.text or "N/A"

            pattern = row_data.get("dnorpattern", "N/A")
            description = row_data.get("description", "N/A")
            pattern_type = row_data.get("pattern_type", "N/A")
            partition = row_data.get("partition_name", "N/A")

            match_number = len(matches) + 1

            matches.append(
                f"""{match_number}.
            Pattern: {pattern}
            Type: {pattern_type}
            Partition: {partition}
            Description: {description}"""
            )

        matches_text = "\n\n".join(matches[:10])

        extra_note = ""
        if len(matches) > 10:
            extra_note = f"\n\nShowing first 10 of {len(matches)} matches."

        return f"""🔎 CUCM Route Plan Lookup: {search_value}

Search Terms:
{", ".join(search_terms)}

Matches Found: {len(matches)}

{matches_text}{extra_note}

⚠️ If a pattern exists here, it should not be considered free for assignment."""

    except Exception as e:
        return f"""❌ CUCM route plan lookup failed.

Pattern: {search_value}
CUCM Host: {CUCM_HOST}

Error Type: {type(e).__name__}
Error:
{str(e)}"""