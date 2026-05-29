# app/utils/formatting.py
"""
Webex message formatting helpers.

Webex supports a subset of Markdown:
  **bold**, `inline code`, ``` code blocks ```, headers (#), bullet lists.

Keep these helpers simple — they produce clean plaintext that also reads
well when Markdown is disabled in the client.
"""


def bold(text: str) -> str:
    """Return text wrapped in Webex bold markers."""
    return f"**{text}**"


def code(text: str) -> str:
    """Return text as inline code."""
    return f"`{text}`"


def code_block(text: str) -> str:
    """Return text as a fenced code block."""
    return f"```\n{text}\n```"


def section(title: str, body: str = "") -> str:
    """Return a section with a bold header and optional body."""
    lines = [bold(title)]
    if body:
        lines.append(body)
    return "\n".join(lines)


def divider() -> str:
    """Return a visual divider line."""
    return "━" * 40


def field(label: str, value: str, width: int = 16) -> str:
    """Return a key: value line with consistent label width."""
    return f"{label:<{width}}{value}"


def status_icon(state: str) -> str:
    """
    Map a generic state string to an emoji status icon.

    Covers common states across CUCM, network, and vSphere.
    """
    state_lower = (state or "").lower()

    if state_lower in ("registered", "up", "active", "online", "connected",
                       "synchronized", "poweredon", "success", "enabled"):
        return "✅"
    if state_lower in ("unregistered", "down", "inactive", "offline",
                       "disconnected", "failed", "disabled"):
        return "❌"
    if state_lower in ("unknown", "partial", "degraded", "warning"):
        return "⚠️"
    if state_lower in ("passive", "standby"):
        return "🔄"

    return "❓"
