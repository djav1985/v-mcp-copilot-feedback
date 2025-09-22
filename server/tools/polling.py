"""Shared polling metadata helpers for MCP tools."""

from __future__ import annotations

POLL_INSTRUCTIONS_TEMPLATE = "Poll the reply resource every {seconds} seconds for the answer."
REPLY_RESOURCE_TEMPLATE = "resource://get_reply/{question_id}/{auth_key}"
REPLY_TOOL_NAME = "get_reply"


def build_poll_metadata(poll_interval_seconds: int) -> dict[str, int | str]:
    """Return polling metadata shared by MCP tools."""

    return {
        "poll_interval_seconds": poll_interval_seconds,
        "poll_instructions": POLL_INSTRUCTIONS_TEMPLATE.format(seconds=poll_interval_seconds),
        "reply_tool": REPLY_TOOL_NAME,
        "reply_resource_template": REPLY_RESOURCE_TEMPLATE,
    }
