# app/state/pending_actions.py

"""
Temporary in-memory pending actions for interactive Webex bot replies.

Each entry stores the action payload plus a 'created_at' timestamp.
Entries older than PENDING_TTL_SECONDS are silently discarded so a
stale "yes" or number reply from a previous session cannot trigger
an unintended action.
"""

import time
from typing import Optional

PENDING_ACTIONS: dict = {}

# 5-minute TTL — entries older than this are expired
PENDING_TTL_SECONDS = 300


def set_pending(email: str, action: dict) -> None:
    """Store a pending action for a user, stamping creation time."""
    action["created_at"] = time.time()
    PENDING_ACTIONS[email] = action


def get_pending(email: str) -> Optional[dict]:
    """Return the pending action if it exists and is not expired; else None."""
    entry = PENDING_ACTIONS.get(email)
    if not entry:
        return None
    age = time.time() - entry.get("created_at", 0)
    if age > PENDING_TTL_SECONDS:
        PENDING_ACTIONS.pop(email, None)
        return None
    return entry


def clear_pending(email: str) -> None:
    """Remove the pending action for a user."""
    PENDING_ACTIONS.pop(email, None)
