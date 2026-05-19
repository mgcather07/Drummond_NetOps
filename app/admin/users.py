from app.database.sql import get_sql_connection
from app.security.auth import get_user_role


VALID_ROLES = ["master", "admin", "user"]


def require_master(sender_email: str) -> bool:
    return get_user_role(sender_email) == "master"


def list_users(sender_email: str) -> str:
    if not require_master(sender_email):
        return "⛔ You do not have permission to view bot users."

    conn = get_sql_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT email, name, role_name, enabled
        FROM dbo.users
        ORDER BY role_name, name
        """
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "👥 No bot users found."

    grouped_users = {
        "master": [],
        "admin": [],
        "user": [],
    }

    for row in rows:
        role = row.role_name.lower()


        line = f"{row.name} | {row.email}"

        if role in grouped_users:
            grouped_users[role].append(line)
        else:
            grouped_users.setdefault(role, []).append(line)

    def format_group(title: str, users: list) -> str:
        if not users:
            return f"{title}\n- None"

        user_lines = "\n".join([f"- {user}" for user in users])

        return f"{title}\n{user_lines}"

    return f"""👥 Bot Authorized Users

{format_group("Master", grouped_users.get("master", []))}

{format_group("Admin", grouped_users.get("admin", []))}

{format_group("User", grouped_users.get("user", []))}"""


def add_user(command: str, sender_email: str) -> str:
    if not require_master(sender_email):
        return "⛔ You do not have permission to add bot users."

    parts = command.split()

    if len(parts) < 5:
        return "Usage: /admin add-user <email> <role> <name>"

    email = parts[2].lower()
    role = parts[3].lower()
    name = " ".join(parts[4:])

    if role not in VALID_ROLES:
        return f"❌ Invalid role: {role}\n\nValid roles: master, admin, user"

    conn = get_sql_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO dbo.users (
                email,
                name,
                role_name,
                enabled
            )
            VALUES (?, ?, ?, 1)
            """,
            (email, name, role)
        )

        conn.commit()

        return f"""✅ User Added

Name: {name}
Email: {email}
Role: {role}
Enabled: True"""

    except Exception as e:
        return f"""❌ Failed to add user.

Email: {email}
Error: {str(e)}"""

    finally:
        conn.close()


def disable_user(command: str, sender_email: str) -> str:
    if not require_master(sender_email):
        return "⛔ You do not have permission to disable bot users."

    parts = command.split()

    if len(parts) < 3:
        return "Usage: /admin disable-user <email>"

    email = parts[2].lower()

    conn = get_sql_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE dbo.users
        SET enabled = 0
        WHERE LOWER(email) = LOWER(?)
        """,
        (email,)
    )

    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()

    if rows_updated == 0:
        return f"❌ No user found with email: {email}"

    return f"""✅ User Disabled

Email: {email}"""


def enable_user(command: str, sender_email: str) -> str:
    if not require_master(sender_email):
        return "⛔ You do not have permission to enable bot users."

    parts = command.split()

    if len(parts) < 3:
        return "Usage: /admin enable-user <email>"

    email = parts[2].lower()

    conn = get_sql_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE dbo.users
        SET enabled = 1
        WHERE LOWER(email) = LOWER(?)
        """,
        (email,)
    )

    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()

    if rows_updated == 0:
        return f"❌ No user found with email: {email}"

    return f"""✅ User Enabled

Email: {email}"""


def set_user_role(command: str, sender_email: str) -> str:
    if not require_master(sender_email):
        return "⛔ You do not have permission to change bot user roles."

    parts = command.split()

    if len(parts) < 4:
        return "Usage: /admin set-role <email> <role>"

    email = parts[2].lower()
    role = parts[3].lower()

    if role not in VALID_ROLES:
        return f"❌ Invalid role: {role}\n\nValid roles: master, admin, user"

    conn = get_sql_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE dbo.users
        SET role_name = ?
        WHERE LOWER(email) = LOWER(?)
        """,
        (role, email)
    )

    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()

    if rows_updated == 0:
        return f"❌ No user found with email: {email}"

    return f"""✅ User Role Updated

Email: {email}
Role: {role}"""


def handle_admin_user_command(command: str, sender_email: str) -> str:
    command_lower = command.lower().strip()

    if command_lower == "/admin users":
        return list_users(sender_email)

    if command_lower.startswith("/admin add-user"):
        return add_user(command, sender_email)

    if command_lower.startswith("/admin disable-user"):
        return disable_user(command, sender_email)

    if command_lower.startswith("/admin enable-user"):
        return enable_user(command, sender_email)

    if command_lower.startswith("/admin set-role"):
        return set_user_role(command, sender_email)

    return """Admin User Commands

/admin users
/admin add-user <email> <role> <name>
/admin disable-user <email>
/admin enable-user <email>
/admin set-role <email> <role>"""