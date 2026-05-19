# app/state/pending_actions.py

"""
Temporary in-memory pending actions for interactive Webex bot replies.

Example:
User runs:
    /cucm phones-eol

Bot stores:
    {
        "user@email.com": {
            "type": "phone_lifecycle_model_select",
            "models": ["Cisco 7811", "Cisco 7941"]
        }
    }

Then user replies:
    2

Bot uses the stored action to know which model they selected.
"""

PENDING_ACTIONS = {}