TRUNKS = {
    "LPUC_ATT": {
        "name": "LPUC-CUBE-SIP-ATT",
        "aliases": ["LPUC", "ATT", "LPUC_ATT", "LPUC-CUBE", "CUBE"],
        "provider": "AT&T",
        "site": "LPUC",
        "type": "CUBE SIP Trunk",
    },

    "JSP_B3_CUBE": {
        "name": "CUCM-SIP-JSP-B3-R1-Cube",
        "aliases": ["JSP", "JASPER", "JSP_B3", "B3", "JASPER_B3"],
        "provider": "CUBE",
        "site": "JASPER",
        "type": "CUBE SIP Trunk",
    },
}


def normalize_trunk_name(trunk_input: str):
    if not trunk_input:
        return None

    cleaned = (
        trunk_input
        .strip()
        .upper()
        .replace(" ", "_")
        .replace("-", "_")
    )

    if cleaned in TRUNKS:
        return cleaned

    for trunk_key, trunk_data in TRUNKS.items():
        aliases = trunk_data.get("aliases", [])

        normalized_aliases = [
            alias.upper().replace(" ", "_").replace("-", "_")
            for alias in aliases
        ]

        if cleaned in normalized_aliases:
            return trunk_key

    return None


def get_trunk(trunk_input: str):
    trunk_key = normalize_trunk_name(trunk_input)

    if not trunk_key:
        return None

    trunk = TRUNKS[trunk_key].copy()
    trunk["key"] = trunk_key

    return trunk