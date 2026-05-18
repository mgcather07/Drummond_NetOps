AUTHORIZED_USERS = {
    "mcather@drummondco.com": {
        "name": "Michael Cather",
        "role": "master",
    },

    "voice.engineer@drummondco.com": {
        "name": "Voice Engineer",
        "role": "voice_admin",
    },

    "helpdesk.user@drummondco.com": {
        "name": "Help Desk",
        "role": "readonly",
    },
}


ROLE_PERMISSIONS = {
    "master": ["*"],

    "voice_admin": [
        "help",
        "status",
        "cucm",
        "network_read",
    ],

    "readonly": [
        "help",
        "status",
        "cucm_read",
    ],
}