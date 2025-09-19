#!/usr/bin/env python3
"""
Test script for MCP Server functionality
"""

import json
import sys
import os

# Add the current directory to the path to import mcp_server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import MCPServer
import asyncio

async def test_mcp_server():
    """Test the MCP server functionality."""
    server = MCPServer()
    
    print("Testing MCP Server...")
    
    # Test initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = await server.handle_request(init_request)
    print("Initialize response:", json.dumps(response, indent=2))
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    
    # Test tools/list
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await server.handle_request(list_tools_request)
    print("\nTools list response:", json.dumps(response, indent=2))
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) == 3  # Should have 3 tools
    
    # Verify tools are properly structured
    tools = response["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    expected_tools = ["ask_user_question", "request_code_review", "get_user_preference"]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
    
    print("\n✅ All tests passed! MCP Server is working correctly.")
    print("Available tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())