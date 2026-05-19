# app/data/phone_eol_catalog.py

"""
Cisco phone / endpoint EOL catalog for Drummond NetOps.

This catalog is based on Cisco published EOL/EOS notices and Cisco support
listing pages, not on the device count summary from CUCM.

Status meanings:
    supported          = No current Cisco EOL notice found in the checked Cisco docs.
    eol_announced      = Cisco has announced EOL/EOS, but end-of-sale has not passed yet.
    end_of_sale        = Past Cisco end-of-sale, but support may still remain.
    end_of_support     = Past Cisco last date of support / retired / obsolete.
    not_hardware_phone = CUCM software/client/device-profile type, not a physical phone refresh item.
    third_party        = Not Cisco hardware; check actual vendor/model.
    unknown            = Needs manual verification.

Risk meanings:
    critical = Replace / remove from production planning immediately.
    high     = Include in refresh planning now.
    medium   = Watch list / verify model details.
    low      = No immediate action.

Date context:
    This catalog was updated against Cisco docs as of 2026-05-19.
    Older unsupported devices with no precise Cisco support date use "Expired" for boss-friendly reporting.
"""

PHONE_EOL_CATALOG = {
    # -----------------------------
    # Cisco 6900 Series
    # -----------------------------

    "Cisco 6901": {
        "status": "eol_announced",
        "risk": "medium",
        "eol_announcement_date": "2026-04-29",
        "end_of_sale_date": "2026-10-28",
        "last_date_of_support": "2031-10-31",
        "replacement": "Cisco Desk Phone 9800 Series / current Cisco desk phone",
        "source": "Cisco EOL15896 - Cisco Unified IP Phone 6901",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-6900-series/unified-ip-phone-6901-eol.html",
        "notes": "Cisco has announced EOL/EOS, but the phone is not currently unsupported. Last date of support is 2031-10-31.",
    },

    "Cisco 6921": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2013-10-30",
        "end_of_sale_date": "2014-07-30",
        "last_date_of_support": "2019-07-31",
        "replacement": "Cisco Desk Phone 9800 Series / Cisco 8800 Series if already standardized",
        "source": "Cisco EOL9421 - Cisco Unified IP Phone 6911, 6921, 6941, 6945, and 6961",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-6900-series/eos-eol-notice-c51-730096.html",
        "notes": "Past Cisco last date of support. Treat as unsupported hardware.",
    },

    # -----------------------------
    # Cisco 7800 Series
    # -----------------------------

    "Cisco 7811": {
        "status": "eol_announced",
        "risk": "medium",
        "eol_announcement_date": "2026-04-29",
        "end_of_sale_date": "2026-10-28",
        "last_date_of_support": "2031-10-31",
        "replacement": "Cisco Desk Phone 9841 / current Cisco desk phone",
        "source": "Cisco EOL notice - Cisco IP Phone 7811",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-7800-series/ip-phone-7811-eol.html",
        "notes": "EOL announced, but Cisco support remains available until 2031-10-31. Do not report as currently unsupported.",
    },

    "Cisco 7821": {
        "status": "eol_announced",
        "risk": "medium",
        "eol_announcement_date": "2026-05-13",
        "end_of_sale_date": "2026-10-28",
        "last_date_of_support": "2031-10-31",
        "replacement": "Cisco Desk Phone 9841 / current Cisco desk phone",
        "source": "Cisco EOL15900 - Cisco IP Phone 7821",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-7800-series/ip-phone-7821-eol.html",
        "notes": "EOL announced, but Cisco support remains available until 2031-10-31. Use this for lifecycle planning, not emergency replacement.",
    },

    "Cisco 7832": {
        "status": "eol_announced",
        "risk": "medium",
        "eol_announcement_date": "2026-04-29",
        "end_of_sale_date": "2026-10-28",
        "last_date_of_support": "2031-10-31",
        "replacement": "Cisco 8832 / Cisco Desk Phone 9800 Series conference option",
        "source": "Cisco EOL notice - Cisco IP Conference Phone 7832",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-7800-series/ip-conference-phone-7832-eol.html",
        "notes": "EOL announced, but Cisco support remains available until 2031-10-31.",
    },

    "Cisco 7841": {
        "status": "supported",
        "risk": "low",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Cisco 7800 Series EOL listing checked; no 7841 EOL notice found during this pass",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7800-series/eos-eol-notice-listing.html",
        "notes": "No Cisco EOL notice found for 7841 in the checked Cisco 7800 Series EOL listing.",
    },

    # -----------------------------
    # Cisco 7900 Series
    # -----------------------------

    "Cisco 7911": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2013-12-22",
        "end_of_sale_date": None,
        "last_date_of_support": "Expired",
        "replacement": "Cisco Desk Phone 9800 Series / Cisco 8800 Series if already standardized",
        "source": "Cisco 7900 Series EOL listing - Cisco Unified IP Phone 7911G",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-listing.html",
        "notes": "Cisco lists a 7911G EOL notice. Treat as unsupported legacy 7900-series hardware.",
    },

    "Cisco 7936": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": "Expired",
        "replacement": "Cisco 8832 / current Cisco conference phone",
        "source": "Cisco 7900 Series support/EOL references",
        "source_url": "https://www.cisco.com/c/en/us/support/collaboration-endpoints/unified-ip-phone-7900-series/series.html",
        "notes": "Old conference station. Cisco 7900 Series is no longer supported. Treat as unsupported.",
    },

    "Cisco 7937": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2013-09-30",
        "end_of_sale_date": "2014-03-31",
        "last_date_of_support": "Expired",
        "replacement": "Cisco 8832 / current Cisco conference phone",
        "source": "Cisco EOL notice - Cisco Unified IP Conference Station 7937G",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-7940g/end_of_life_notice_c51-729487.html",
        "notes": "Old conference station. Treat as unsupported replacement candidate.",
    },

    "Cisco 7940": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2010-01-22",
        "end_of_sale_date": "2010-07-23",
        "last_date_of_support": "Expired",
        "replacement": "Cisco Desk Phone 9841 / 9851",
        "source": "Cisco 7900 Series EOL listing - Cisco Unified IP Phones 7940G and 7960G",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-listing.html",
        "notes": "Very old 7900-series phone. Treat as unsupported hardware.",
    },

    "Cisco 7941": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2010-08-06",
        "end_of_sale_date": None,
        "last_date_of_support": "Expired",
        "replacement": "Cisco Desk Phone 9841 / 9851",
        "source": "Cisco 7900 Series EOL listing - 7941G-GE hardware notice",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-listing.html",
        "notes": "CUCM may show the model without the G/GE suffix. Verify exact hardware if needed, but treat as unsupported 7900-series hardware.",
    },

    "Cisco 7942": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2015-08-03",
        "end_of_sale_date": "2016-02-01",
        "last_date_of_support": "2021-01-31",
        "replacement": "Cisco Desk Phone 9841 / 9851",
        "source": "Cisco EOL notice - Cisco Unified IP Phones 7915, 7942, and 7962",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-c51-735570.html",
        "notes": "Past Cisco last date of support.",
    },

    "Cisco 7960": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2010-01-22",
        "end_of_sale_date": "2010-07-23",
        "last_date_of_support": "Expired",
        "replacement": "Cisco Desk Phone 9851 / 9861",
        "source": "Cisco 7900 Series EOL listing - Cisco Unified IP Phones 7940G and 7960G",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-listing.html",
        "notes": "Very old 7900-series phone. Treat as unsupported hardware.",
    },

    "Cisco 7961": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2010-08-06",
        "end_of_sale_date": None,
        "last_date_of_support": "Expired",
        "replacement": "Cisco Desk Phone 9851 / 9861",
        "source": "Cisco 7900 Series EOL listing - 7961G-GE hardware notice",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-listing.html",
        "notes": "CUCM may show the model without the G/GE suffix. Verify exact hardware if needed, but treat as unsupported 7900-series hardware.",
    },

    "Cisco 7962": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2015-08-03",
        "end_of_sale_date": "2016-02-01",
        "last_date_of_support": "2021-01-31",
        "replacement": "Cisco Desk Phone 9851 / 9861",
        "source": "Cisco EOL notice - Cisco Unified IP Phones 7915, 7942, and 7962",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-c51-735570.html",
        "notes": "Past Cisco last date of support.",
    },

    # -----------------------------
    # Cisco Wireless / 800 Series
    # -----------------------------

    "Cisco 840": {
        "status": "end_of_sale",
        "risk": "high",
        "eol_announcement_date": "2025-10-14",
        "end_of_sale_date": "2025-11-28",
        "last_date_of_support": "2028-11-30",
        "replacement": "Cisco Wireless Phone 860 / current wireless option",
        "source": "Cisco EOL15765 - Cisco Wireless Phone 840",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/webex-wireless-phone/wireless-phone-840-eol.html",
        "notes": "Past end-of-sale, but not past final support. Include in refresh planning.",
    },

    # -----------------------------
    # Cisco 8800 Series
    # -----------------------------

    "Cisco 8811": {
        "status": "supported",
        "risk": "low",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Cisco 8800 Series EOL listing checked; no 8811 EOL notice found during this pass",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-8800-series/eos-eol-notice-listing.html",
        "notes": "No Cisco EOL notice found for 8811 in the checked Cisco 8800 Series EOL listing.",
    },

    "Cisco 8831": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2019-04-08",
        "end_of_sale_date": "2019-10-07",
        "last_date_of_support": "2024-10-31",
        "replacement": "Cisco 8832 / current Cisco conference phone",
        "source": "Cisco EOL12402 - Cisco IP Conference Phone 8831",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-conference-phone-8831/eos-eol-notice-c51-741241.html",
        "notes": "Past Cisco last date of support.",
    },

    "Cisco 8832": {
        "status": "supported",
        "risk": "low",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Cisco 8800 Series EOL listing checked; only 8832 white color version has a current EOL notice",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-8800-series/eos-eol-notice-listing.html",
        "notes": "Standard 8832 remains classified as supported. If the unit is specifically the white color version, classify separately as Cisco 8832 White.",
    },

    "Cisco 8832 White": {
        "status": "eol_announced",
        "risk": "medium",
        "eol_announcement_date": "2026-04-29",
        "end_of_sale_date": "2026-10-28",
        "last_date_of_support": "2031-10-31",
        "replacement": "Cisco 8832 standard color / current Cisco conference phone",
        "source": "Cisco EOL notice - Cisco IP Conference Phone 8832 white color version",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-8800-series/ip-conf-phone-8832-white-eol.html",
        "notes": "Only the white color version is covered by this notice. Do not apply this automatically to all 8832 phones unless you can identify the white version.",
    },

    "Cisco 8841": {
        "status": "supported",
        "risk": "low",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Cisco 8800 Series EOL listing checked; no 8841 EOL notice found during this pass",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-8800-series/eos-eol-notice-listing.html",
        "notes": "No Cisco EOL notice found for 8841 in the checked Cisco 8800 Series EOL listing.",
    },

    "Cisco 8851": {
        "status": "supported",
        "risk": "low",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Cisco 8800 Series EOL listing checked; no 8851 EOL notice found during this pass",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-8800-series/eos-eol-notice-listing.html",
        "notes": "No Cisco EOL notice found for 8851 in the checked Cisco 8800 Series EOL listing.",
    },

    "Cisco 8851NR": {
        "status": "supported",
        "risk": "low",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Cisco 8800 Series EOL listing checked; no 8851NR EOL notice found during this pass",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-8800-series/eos-eol-notice-listing.html",
        "notes": "Treat same as 8851 unless a specific NR notice is found.",
    },

    "Cisco 8865": {
        "status": "end_of_sale",
        "risk": "high",
        "eol_announcement_date": "2025-02-26",
        "end_of_sale_date": "2025-04-26",
        "last_date_of_support": "2030-07-31",
        "replacement": "Cisco Video Phone 8875 / Cisco Desk Phone 9800 Series video-capable alternative",
        "source": "Cisco EOL15614 - Cisco Video Phone 8865",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/unified-ip-phone-8800-series/video-phone-8865-eol.html",
        "notes": "Past end-of-sale, but Cisco support remains available until 2030-07-31.",
    },

    # -----------------------------
    # Cisco ATA
    # -----------------------------

    "Cisco ATA 186": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": "Expired",
        "replacement": "Cisco ATA 191 / ATA 192 or supported analog gateway",
        "source": "Cisco 7900 Series / ATA 186 retirement references",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/unified-ip-phone-7900-series/eos-eol-notice-listing.html",
        "notes": "Legacy ATA. Treat as unsupported unless you verify a newer supported adapter is actually deployed.",
    },

    "Cisco ATA 190": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": "2018-09-14",
        "end_of_sale_date": "2019-03-15",
        "last_date_of_support": "2024-03-31",
        "replacement": "Cisco ATA 191",
        "source": "Cisco EOL notice - Cisco ATA 190 Analog Telephone Adapter",
        "source_url": "https://www.cisco.com/c/en/us/products/collateral/collaboration-endpoints/ata-190-series-analog-telephone-adapters/ata-190-eol.html",
        "notes": "Past Cisco last date of support.",
    },

    # -----------------------------
    # Video endpoint
    # -----------------------------

    "Cisco TelePresence SX20": {
        "status": "end_of_support",
        "risk": "critical",
        "eol_announcement_date": None,
        "end_of_sale_date": "2020-01-28",
        "last_date_of_support": "2025-01-31",
        "replacement": "Cisco Room Bar / Room Kit / current Webex Room endpoint",
        "source": "Cisco TelePresence SX Series retirement/EOL references",
        "source_url": "https://www.cisco.com/c/en/us/products/collaboration-endpoints/telepresence-sx-series/eos-eol-notice-listing.html",
        "notes": "Cisco SX Series endpoint. Treat as unsupported if still in production.",
    },

    # -----------------------------
    # Software / virtual endpoint types
    # -----------------------------

    "Cisco Jabber for Tablet": {
        "status": "not_hardware_phone",
        "risk": "medium",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": "Webex App",
        "source": "Internal classification",
        "source_url": None,
        "notes": "Software client. Do not count as physical phone refresh, but useful for client migration reporting.",
    },

    "Cisco Unified Client Services Framework": {
        "status": "not_hardware_phone",
        "risk": "medium",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": "Webex App",
        "source": "Internal classification",
        "source_url": None,
        "notes": "Jabber CSF softphone device type. Do not count as physical phone refresh.",
    },

    "Cisco Spark Remote Device": {
        "status": "not_hardware_phone",
        "risk": "medium",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": "Webex App / Webex Calling architecture",
        "source": "Internal classification",
        "source_url": None,
        "notes": "Remote device profile type, not physical phone hardware.",
    },

    "Third-party SIP Device (Basic)": {
        "status": "third_party",
        "risk": "unknown",
        "eol_announcement_date": None,
        "end_of_sale_date": None,
        "last_date_of_support": None,
        "replacement": None,
        "source": "Internal classification",
        "source_url": None,
        "notes": "Not Cisco hardware. EOL must be checked against the actual vendor/model.",
    },
}


NON_PHONE_DEVICE_TYPES = {
    "CTI Port",
    "CTI Route Point",
    "Cisco IOS Conference Bridge (HDV2)",
    "Cisco IOS Media Termination Point (HDV2)",
    "Cisco IOS Software Media Termination Point (HDV2)",
    "Cisco VGC Phone",
    "Conference Bridge",
    "GateKeeper",
    "H.323 Gateway",
    "Interactive Voice Response",
    "MGCP Station",
    "MGCP Trunk",
    "Media Termination Point",
    "Music On Hold",
    "Remote Destination Profile",
    "Route List",
    "SIP Trunk",
    "Tone Announcement Player",
    "Trunk",
    "Universal Device Template",
    "Voice Mail Port",
}