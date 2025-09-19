from __future__ import annotations

import asyncio

from server.mcp_server import get_mcp_server, reload_server


def _gather_tools():
    server = reload_server()
    return asyncio.run(server.list_tools())


def _gather_resource_templates():
    server = get_mcp_server()
    return asyncio.run(server.list_resource_templates())


def test_ask_question_tool_registered():
    tools = _gather_tools()
    tool_names = {tool.name for tool in tools}
    assert "ask_question" in tool_names


def test_get_reply_resource_registered():
    resources = _gather_resource_templates()
    resource_uris = {resource.uriTemplate for resource in resources}
    assert "resource://get_reply/{question_id}/{auth_key}" in resource_uris

