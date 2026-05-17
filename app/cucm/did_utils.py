from app.data.did_blocks import DID_BLOCKS


def expand_did_ranges(site_name: str) -> list:
    """
    Expands configured DID ranges into full 10-digit numbers.
    """

    site_name = site_name.upper()

    if site_name not in DID_BLOCKS:
        return []

    all_dids = []

    for block in DID_BLOCKS[site_name]:

        npa = block["npa"]
        nxx = block["nxx"]

        low = int(block["low"])
        high = int(block["high"])

        for number in range(low, high + 1):

            did = f"{npa}{nxx}{number:04d}"
            all_dids.append(did)

    return all_dids