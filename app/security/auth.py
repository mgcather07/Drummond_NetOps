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


COMMAND_PERMISSIONS = {
    # -----------------------------
    # Admin user management
    # -----------------------------
    "/admin users": "admin.users.master",
    "/admin add-user": "admin.users.master",
    "/admin disable-user": "admin.users.master",
    "/admin enable-user": "admin.users.master",
    "/admin set-role": "admin.users.master",

    # -----------------------------
    # CUCM read-only commands
    # -----------------------------
    "/cucm phone": "cucm.read",
    "/cucm extension": "cucm.read",
    "/cucm free-extension": "cucm.read",
    "/cucm trunk": "cucm.read",
    "/cucm route-plan": "cucm.read",
    "/cucm did-search": "cucm.read",
    "/cucm call flow": "cucm.read",

    # -----------------------------
    # CUCM health commands
    # -----------------------------
    "/cucm health": "cucm.health",
    "/cucm dbreplication": "cucm.health",
    "/cucm services": "cucm.health",
    "/cucm sip-trunk status": "cucm.health",

    # -----------------------------
    # Network read-only commands
    # -----------------------------
    "/ping": "network.read",
    "/network ping": "network.read",
    "/network show-version": "network.read",
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


def normalize_role(role: Optional[str]) -> Optional[str]:

    if not role:
        return None

    return role.lower().strip()


def has_permission(email: str, permission: str) -> bool:

    role = normalize_role(get_user_role(email))

    if not role:
        return False

    permissions = ROLE_PERMISSIONS.get(role, [])

    return "*" in permissions or permission in permissions


def get_command_permission(command: str) -> Optional[str]:

    command_lower = command.lower().strip()

    # Match longest command first so specific commands win.
    # Example: /cucm sip-trunk status should match before /cucm.
    for command_prefix in sorted(COMMAND_PERMISSIONS.keys(), key=len, reverse=True):
        if command_lower.startswith(command_prefix):
            return COMMAND_PERMISSIONS[command_prefix]

    return None


def can_run_command(email: str, command: str) -> bool:

    permission = get_command_permission(command)

    # If a command is not listed, do not block it here.
    # This lets public commands like /help still work.
    if not permission:
        return True

    return has_permission(email, permission)


def command_permission_denied_message(email: str, command: str) -> str:

    permission = get_command_permission(command)

    return f"""⛔ Permission Denied

You are authorized to use Drummond NetOps Bot, but your role does not allow this command.

Email: {email}
Command: {command}
Required Permission: {permission}"""


def unauthorized_message(email: str) -> str:

    return f"""⛔ Access Denied

Your account is not authorized to use Drummond NetOps Bot.

Email: {email}

If you believe this is incorrect, contact an administrator."""