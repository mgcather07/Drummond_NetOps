from app.data.authorized_users import AUTHORIZED_USERS, ROLE_PERMISSIONS
from typing import Optional


def get_user(email: str) -> Optional[dict]:
    if not email:
        return None

    return AUTHORIZED_USERS.get(email.lower())


def is_authorized(email: str) -> bool:
    return get_user(email) is not None

def get_user_role(email: str) -> Optional[str]:
    user = get_user(email)

    if not user:
        return None

    return user.get("role")


def has_permission(email: str, permission: str) -> bool:
    role = get_user_role(email)

    if not role:
        return False

    permissions = ROLE_PERMISSIONS.get(role, [])

    return "*" in permissions or permission in permissions


def unauthorized_message(email: str) -> str:
    return f"""⛔ Access Denied

Your account is not authorized to use Drummond NetOps Bot.

Email: {email}

If you believe this is incorrect, contact an administrator."""