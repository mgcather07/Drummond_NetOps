from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
import logging
logger = logging.getLogger(__name__)
import os
import requests
from collections import defaultdict
from typing import Optional

from app.data.phone_eol_catalog import PHONE_EOL_CATALOG, NON_PHONE_DEVICE_TYPES

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_USERNAME = os.getenv("CUCM_USERNAME")
CUCM_PASSWORD = os.getenv("CUCM_PASSWORD")

requests.packages.urllib3.disable_warnings()


EOL_STATUSES = {
    "eol_announced",
    "end_of_sale",
    "end_of_support",
}


def get_risk_icon(risk: str) -> str:
    risk = (risk or "").lower()

    if risk == "critical":
        return "🔴"
    if risk == "high":
        return "🟠"
    if risk == "medium":
        return "🟡"
    if risk == "low":
        return "🟢"

    return "⚪"


def get_status_label(status: str) -> str:
    labels = {
        "eol_announced": "EOL Announced",
        "end_of_sale": "End of Sale",
        "end_of_support": "End of Support",
        "supported": "Supported",
        "unknown": "Unknown",
    }

    return labels.get(status, status or "Unknown")


def get_axl_service():
    axl_url = f"https://{CUCM_HOST}:8443/axl/"

    session = requests.Session()
    session.verify = False
    session.auth = HTTPBasicAuth(CUCM_USERNAME, CUCM_PASSWORD)

    transport = Transport(session=session, timeout=60)

    client = Client(
        wsdl="schema/15.0/AXLAPI.wsdl",
        transport=transport
    )

    return client.create_service(
        "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
        axl_url
    )


def row_to_dict(row) -> dict:
    if not isinstance(row, list):
        row = [row]

    data = {}

    for column in row:
        if hasattr(column, "tag"):
            data[column.tag] = column.text or ""

    return data


def get_live_phone_inventory() -> list:
    service = get_axl_service()

    sql = """
    SELECT
        d.name AS device_name,
        d.description,
        tm.name AS model,
        n.dnorpattern AS extension,
        dp.name AS device_pool
    FROM device d
    LEFT JOIN typemodel tm
        ON d.tkmodel = tm.enum
    LEFT JOIN devicepool dp
        ON d.fkdevicepool = dp.pkid
    LEFT JOIN devicenumplanmap dnpm
        ON dnpm.fkdevice = d.pkid
    LEFT JOIN numplan n
        ON dnpm.fknumplan = n.pkid
    WHERE d.name LIKE 'SEP%'
    ORDER BY tm.name, d.name
    """

    response = service.executeSQLQuery(sql=sql)
    data = serialize_object(response)

    result = data.get("return")

    if not result:
        return []

    rows = result.get("row", [])

    if not rows:
        return []

    if not isinstance(rows, list):
        rows = [rows]

    phones = []

    for row in rows:
        row_data = row_to_dict(row)

        model = row_data.get("model", "Unknown")

        if model in NON_PHONE_DEVICE_TYPES:
            continue

        phones.append({
            "device_name": row_data.get("device_name", "N/A"),
            "extension": row_data.get("extension", "N/A"),
            "description": row_data.get("description", "N/A"),
            "model": model,
            "device_pool": row_data.get("device_pool", "N/A"),
        })

    return phones


def get_eol_phones() -> list:
    phones = get_live_phone_inventory()
    eol_phones = []

    for phone in phones:
        model = phone.get("model", "Unknown")
        catalog_entry = PHONE_EOL_CATALOG.get(model)

        if not catalog_entry:
            continue

        status = catalog_entry.get("status")

        if status not in EOL_STATUSES:
            continue

        phone["eol"] = catalog_entry
        eol_phones.append(phone)

    return eol_phones


def group_phones_by_model(phones: list) -> dict:
    grouped = defaultdict(list)

    for phone in phones:
        grouped[phone["model"]].append(phone)

    return dict(grouped)


def build_phone_eol_summary(grouped: dict, sender_email: str, pending_actions: dict) -> str:
    status_order = {
        "end_of_support": 1,
        "end_of_sale": 2,
        "eol_announced": 3,
    }

    category_labels = {
        "end_of_support": "Unsupported / Replace First",
        "end_of_sale": "End of Sale / Refresh Planning",
        "eol_announced": "EOL Announced / Still Supported",
    }

    models = sorted(
        grouped.keys(),
        key=lambda model: (
            status_order.get(PHONE_EOL_CATALOG.get(model, {}).get("status"), 99),
            model,
        )
    )


    from app.state.pending_actions import set_pending
    set_pending(sender_email, {
        "type": "phone_lifecycle_model_select",
        "models": models,
    })

    lines = []
    current_status = None

    for index, model in enumerate(models, start=1):
        phones = grouped[model]
        catalog = PHONE_EOL_CATALOG.get(model, {})

        status = catalog.get("status", "unknown")
        last_support = catalog.get("last_date_of_support") or "N/A"

        if status != current_status:
            if lines:
                lines.append("")

            lines.append(f"--- {category_labels.get(status, get_status_label(status))} ---")
            current_status = status


        lines.append(
            f"{index}. {model} - {len(phones)} phones | "
            f"{get_status_label(status)} | Support Ends: {last_support}"
        )

    total_count = sum(len(phones) for phones in grouped.values())
    model_count = len(grouped)

    return f"""📱 CUCM Phones EOL Summary

EOL Phones Found: {total_count}
EOL Models Found: {model_count}

Reply with a number to view phone details:

{chr(10).join(lines)}"""


def build_phone_eol_model_detail(model: str) -> str:
    eol_phones = get_eol_phones()
    grouped = group_phones_by_model(eol_phones)

    phones = grouped.get(model, [])

    if not phones:
        return f"""📱 CUCM Phones EOL Detail

No phones found for:

{model}"""

    catalog = PHONE_EOL_CATALOG.get(model, {})

    risk = catalog.get("risk", "unknown")
    status = catalog.get("status", "unknown")
    replacement = catalog.get("replacement") or "N/A"
    last_support = catalog.get("last_date_of_support") or "N/A"
    source = catalog.get("source") or "N/A"

    MAX_PHONES_PER_MODEL = 25

    section_lines = [
        f"📱 CUCM Phones EOL Detail",
        "",
        f"Model: {model}",
        f"Phones Found: {len(phones)}",
        f"Status: {get_status_label(status)}",
        f"Risk: {get_risk_icon(risk)} {risk.title()}",
        f"Last Date of Support: {last_support}",
        f"Replacement: {replacement}",
        f"Source: {source}",
        "",
        f"{'Device Name':<18} {'Extension':<10} {'Device Pool':<20}",
        f"{'-' * 18} {'-' * 10} {'-' * 20}",
    ]

    sorted_phones = sorted(
        phones,
        key=lambda phone: (
            phone.get("device_pool", ""),
            phone.get("device_name", "")
        )
    )

    for phone in sorted_phones[:MAX_PHONES_PER_MODEL]:
        section_lines.append(
            f"{phone['device_name']:<18} "
            f"{phone['extension']:<10} "
            f"{phone['device_pool'][:20]:<20}"
        )

    if len(phones) > MAX_PHONES_PER_MODEL:
        section_lines.append("")
        section_lines.append(
            f"... showing first {MAX_PHONES_PER_MODEL} of {len(phones)} phones"
        )

    return "\n".join(section_lines)


def get_phones_eol(command: str, sender_email: str, pending_actions: dict) -> str:
    try:
        eol_phones = get_eol_phones()

        if not eol_phones:
            return """📱 CUCM Phones EOL Report

✅ No live CUCM phones matched the EOL catalog."""

        grouped = group_phones_by_model(eol_phones)

        return build_phone_eol_summary(
            grouped=grouped,
            sender_email=sender_email,
            pending_actions=pending_actions,
        )

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Phones EOL report failed")
        return error(translate_exception(e), hint="Check that CUCM AXL is reachable.")

def handle_phone_lifecycle_selection(
            command: str,
            sender_email: str,
            pending_actions: dict
    ) -> Optional[str]:
    from app.state.pending_actions import get_pending, clear_pending
    pending = get_pending(sender_email)

    if not pending:
        return None

    if pending.get("type") != "phone_lifecycle_model_select":
        return None

    command = command.strip()

    if not command.isdigit():
        return "Please reply with the number of the phone model you want to view."

    selection = int(command)
    models = pending.get("models", [])

    if selection < 1 or selection > len(models):
        return f"Please choose a number between 1 and {len(models)}."

    selected_model = models[selection - 1]

    clear_pending(sender_email)

    return build_phone_eol_model_detail(selected_model)