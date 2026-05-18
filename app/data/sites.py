from typing import Optional


SITES = {
    "LPUC": {
        "name": "Liberty Park Urban Center",
        "aliases": ["LPUC", "LIBERTY", "LIBERTY_PARK"],

        # Physical Address
        "address": "1000 Urban Center Drive",
        "city": "Vestavia Hills",
        "state": "AL",
        "zip": "35242",

        # Voice / Network
        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": "LPUC Unlimited",
        "default_location": "LPUC",
    },

    "ABC_COKE": {
        "name": "ABC Coke",
        "aliases": ["ABC", "ABC_COKE", "COKE"],

        "address": "800 Huntsville Ave",
        "city": "Tarrant",
        "state": "AL",
        "zip": "35217",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": "ABC Coke Unlimited",
        "default_location": "ABC Coke Plant",
    },

    "HANGAR": {
        "name": "Hangar",
        "aliases": ["HANGAR"],

        "address": "3800 65th St North",
        "city": "Birmingham",
        "state": "AL",
        "zip": "35206",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "Hangar",
    },

    "SAYRE_MINE": {
        "name": "Sayre Mine",
        "aliases": ["SAYRE", "SAYRE_MINE"],

        "address": "Sayre Mine Rd",
        "city": "Graysville",
        "state": "AL",
        "zip": "35139",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "Sayre Mine",
    },

    "SHANNON_MINE": {
        "name": "Shannon Mine",
        "aliases": ["SHANNON", "SHANNON_MINE"],

        "address": "904 Sayre Mine Rd",
        "city": "Graysville",
        "state": "AL",
        "zip": "35139",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "Shannon Mine",
    },

    "OLD_OVERTON_CLUB": {
        "name": "Old Overton Club",
        "aliases": ["OOC", "OOCC", "OLD_OVERTON"],

        "address": "7251 Old Overton Club Dr",
        "city": "Vestavia Hills",
        "state": "AL",
        "zip": "35242",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "Old Overton Club",
    },

    "PERRY_SUPPLY_MIAMI": {
        "name": "Perry Supply Miami",
        "aliases": ["PSI_MIAMI", "PERRY_MIAMI", "MIAMI"],

        "address": "7494 NW 54th Street",
        "city": "Miami",
        "state": "FL",
        "zip": "33166",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "PSI Miami",
    },

    "RECLAMATION": {
        "name": "Reclamation",
        "aliases": ["RCLM", "RECLAMATION"],

        "address": "1605 Old Russellville Rd",
        "city": "Jasper",
        "state": "AL",
        "zip": "35503",

        "gateway": "LPUC",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "Reclamation",
    },

    "PERRY_SUPPLY_JASPER": {
        "name": "Perry Supply Jasper",
        "aliases": ["PSI_JASPER", "PERRY_JASPER"],

        "address": "205 SW 18th Ave",
        "city": "Jasper",
        "state": "AL",
        "zip": "35501",

        "gateway": "Jasper",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "PSI Jasper",
    },

    "JSP_B1_B2": {
        "name": "Jasper B1/B2",
        "aliases": ["JSP_B1", "JSP_B2", "B1", "B2"],

        "address": "120 N Walston Bridge Rd",
        "city": "Jasper",
        "state": "AL",
        "zip": "35504",

        "gateway": "Jasper",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "JSP B1/B2",
    },

    "MGW": {
        "name": "MGW",
        "aliases": ["MGW"],

        "address": "200 SW 18th Ave",
        "city": "Jasper",
        "state": "AL",
        "zip": "35501",

        "gateway": "Jasper",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "MGW",
    },

    "JSP_LAB": {
        "name": "Jasper Lab",
        "aliases": ["JSP_LAB", "LAB"],

        "address": "2204 Commerce Ave",
        "city": "Jasper",
        "state": "AL",
        "zip": "35501",

        "gateway": "Jasper",
        "default_partition": "Sys-Ext-PT",
        "default_css": None,
        "default_location": "JSP Lab",
    },
}


def normalize_site_name(site_input: str) -> Optional[str]:
    if not site_input:
        return None

    cleaned = (
        site_input
        .strip()
        .upper()
        .replace(" ", "_")
        .replace("-", "_")
    )

    if cleaned in SITES:
        return cleaned

    for site_key, site_data in SITES.items():
        aliases = site_data.get("aliases", [])

        if cleaned in aliases:
            return site_key

    return None


def get_site(site_input: str) -> Optional[dict]:
    site_key = normalize_site_name(site_input)

    if not site_key:
        return None

    site = SITES[site_key].copy()
    site["key"] = site_key

    return site


def list_sites() -> str:
    lines = []

    for site_key, site_data in SITES.items():
        lines.append(
            f"• {site_key} - {site_data['name']}"
        )

    return "\n".join(lines)