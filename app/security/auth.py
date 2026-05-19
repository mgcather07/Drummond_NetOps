from typing import Optional

from app.database.sql import get_sql_connection

ROLE_PERMISSIONS = {
    "master": ["*"],
    "admin": [
        "cucm.read",
        "cucm.health",
        "network.read",
    ],
    "user": [
        "cucm.read",
    ]
}


def get_user(email: str) -> Optional[dict]:

    if not email:
        return None

    try:

        conn = get_sql_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                email,
                name,
                role_name,
                enabled
            FROM dbo.users
            WHERE LOWER(email) = LOWER(?)
            """,
            (email,)
        )

        row = cursor.fetchone()

        conn.close()

        if not row:
            return None

        enabled = bool(row.enabled)

        if not enabled:
            return None

        print("========== AUTH DEBUG ==========")
        print(f"EMAIL: {row.email}")
        print(f"NAME: {row.name}")
        print(f"ROLE: {row.role_name}")
        print(f"ENABLED: {row.enabled}")
        print("================================")

        return {
            "email": row.email,
            "name": row.name,
            "role": row.role_name,
            "enabled": enabled,
        }

    except Exception as e:

        print(f"AUTH SQL ERROR: {e}")

        return None


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