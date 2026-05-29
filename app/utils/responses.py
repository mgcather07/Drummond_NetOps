# app/utils/responses.py
"""
Shared bot response helpers — consistent error and success formatting.

Rules:
  - error()   → never leak exception class names or tracebacks to the user.
                 Log the full detail with logger.exception(), show only the
                 plain-English title (and optional hint) in Webex.
  - success() → concise, emoji-flagged confirmation with optional body.
  - translate_exception() → maps common exception types to plain English.
                             Returns "Unexpected error" for anything else.
"""

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def error(title: str, detail: str = "", hint: str = "") -> str:
    """
    Build a user-facing error message.

    :param title:  Short plain-English description shown to the user.
    :param detail: Technical detail — logged only, NOT sent to the user.
    :param hint:   Optional user-visible suggestion (keep it actionable).
    """
    if detail:
        logger.error("Bot error — %s: %s", title, detail)

    lines = [f"❌ {title}"]
    if hint:
        lines.append(f"\n💡 {hint}")
    return "\n".join(lines)


def success(title: str, body: str = "") -> str:
    """Build a user-facing success message with an optional body."""
    lines = [f"✅ {title}"]
    if body:
        lines.append(body)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Exception translation
# ---------------------------------------------------------------------------

def translate_exception(exc: Exception) -> str:
    """
    Map a caught exception to a plain-English string suitable for users.

    Add new mappings here as new integrations are added (Palo, vSphere, …).
    """
    cls_name = type(exc).__name__
    module = type(exc).__module__ or ""

    # CUCM / Zeep
    if "zeep" in module or cls_name in ("Fault", "TransportError"):
        return "CUCM AXL returned an error"
    if cls_name == "WebFault":
        return "CUCM AXL returned an error"

    # Requests / urllib
    if cls_name == "ConnectionError" or "connection" in cls_name.lower():
        return "Could not reach the remote host"
    if cls_name == "Timeout" or "timeout" in cls_name.lower():
        return "Request timed out"
    if cls_name == "SSLError":
        return "TLS/SSL error connecting to remote host"
    if cls_name == "HTTPError":
        return "HTTP error from remote host"

    # SQL Server / pyodbc
    if "pyodbc" in module or cls_name in ("OperationalError", "ProgrammingError",
                                           "InterfaceError", "DatabaseError"):
        return "SQL Server connection failed"

    # Netmiko / SSH
    if "netmiko" in module:
        if "timeout" in cls_name.lower():
            return "SSH connection timed out"
        if "auth" in cls_name.lower():
            return "SSH authentication failed"
        return "SSH connection failed"
    if "paramiko" in module:
        if "auth" in cls_name.lower():
            return "SSH authentication failed"
        return "SSH error"

    # Webex SDK
    if "webex" in module:
        return "Webex API error"

    return "Unexpected error"
