#!/usr/bin/env python3
"""
Integration test for the MCP server via JSON-RPC communication
"""

import json
import subprocess
import threading
import time
import sys
import os

def test_json_rpc_communication():
    """Test the MCP server via actual JSON-RPC communication."""
    print("Testing MCP Server JSON-RPC communication...")
    
    # Start the server as a subprocess
    server_path = os.path.join(os.path.dirname(__file__), 'mcp_server.py')
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "vibecode-feedback-server"
        print("✅ Initialize test passed")
        
        # Test 2: List tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(list_request) + '\n')
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) == 3
        print("✅ List tools test passed")
        
        # Test 3: Test invalid method (should return error)
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "invalid_method",
            "params": {}
        }
        
        process.stdin.write(json.dumps(invalid_request) + '\n')
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found
        print("✅ Error handling test passed")
        
        print("\n🎉 All JSON-RPC communication tests passed!")
        print("The MCP server is working correctly and ready for use.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_json_rpc_communication()