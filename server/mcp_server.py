"""MCP server definition exposing ask_question and get_reply."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context

from server.tools import ask_question as ask_question_tool
from server.tools import get_reply as get_reply_resource
from server.utility.config import get_config

logger = logging.getLogger(__name__)

_server_instance: FastMCP | None = None


def _build_instructions() -> str:
    config = get_config()
    return (
        "Use the ask_question tool to escalate tricky decisions to a human reviewer. "
        "Always include the X-API-Key header when calling tools or resources. After calling "
        "ask_question, poll resource://get_reply/{question_id}/{auth_key} every "
        f"{config.poll_interval_seconds} seconds until you receive "
        "an answered or expired status. "
        f"Questions expire after {config.question_ttl_seconds} seconds, "
        "returning the fallback reply."
    )


def _create_server() -> FastMCP:
    config = get_config()
    server = FastMCP(
        name="human-handoff-mcp",
        instructions=_build_instructions(),
        host=config.mcp_host,
        port=config.mcp_port,
    )

    @server.tool()
    def ask_question(
        question: str,
        preset_answers: list[str] | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        return ask_question_tool(question=question, preset_answers=preset_answers, ctx=ctx)

    @server.resource("resource://get_reply/{question_id}/{auth_key}")
    def get_reply(
        question_id: str,
        auth_key: str,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        return get_reply_resource(question_id=question_id, auth_key=auth_key, ctx=ctx)

    logger.debug(
        "Configured MCP server on %s:%s", config.mcp_host, config.mcp_port
    )
    return server


def get_mcp_server() -> FastMCP:
    global _server_instance
    if _server_instance is None:
        _server_instance = _create_server()
    return _server_instance


def reload_server() -> FastMCP:
    """Recreate the MCP server using the latest configuration (primarily for tests)."""

    global _server_instance
    _server_instance = _create_server()
    return _server_instance


# Backwards compatibility with documentation that imports `server`
server = get_mcp_server()


def run() -> None:
    """Run the MCP server with the configured transport."""

    config = get_config()
    get_mcp_server().run(transport=config.mcp_transport)

