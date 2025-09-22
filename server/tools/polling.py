"""Shared polling metadata helpers for MCP tools."""

from __future__ import annotations

from typing import TypedDict

POLL_INSTRUCTIONS_TEMPLATE = "Poll the reply resource every {seconds} seconds for the answer."
REPLY_RESOURCE_TEMPLATE = "resource://get_reply/{question_id}/{auth_key}"
REPLY_TOOL_NAME = "get_reply"


class PollMetadata(TypedDict):
    """Typed structure for polling metadata returned by MCP tools."""
    
    poll_interval_seconds: int
    poll_instructions: str
    reply_tool: str
    reply_resource_template: str


def build_poll_metadata(poll_interval_seconds: int) -> PollMetadata:
    """Return polling metadata shared by MCP tools."""

    return {
        "poll_interval_seconds": poll_interval_seconds,
        "poll_instructions": POLL_INSTRUCTIONS_TEMPLATE.format(seconds=poll_interval_seconds),
        "reply_tool": REPLY_TOOL_NAME,
        "reply_resource_template": REPLY_RESOURCE_TEMPLATE,
    }
