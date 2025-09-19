#!/usr/bin/env python3
"""
Test HTTP/HTTPS functionality of the MCP server
"""

import asyncio
import json
import aiohttp
import subprocess
import time
import sys
import os
import signal

async def test_http_server():
    """Test the MCP server in HTTP mode."""
    print("Testing MCP Server HTTP functionality...")
    
    # Start the server in HTTP mode
    server_path = os.path.join(os.path.dirname(__file__), 'mcp_server.py')
    process = subprocess.Popen(
        [sys.executable, server_path, '--mode', 'http', '--port', '8080'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server time to start
    await asyncio.sleep(2)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Health check
            print("Testing health check endpoint...")
            async with session.get('http://localhost:8080/health') as resp:
                assert resp.status == 200
                health_data = await resp.json()
                assert health_data['status'] == 'healthy'
                assert health_data['service'] == 'vibecode-feedback-mcp-server'
                print("✅ Health check test passed")
            
            # Test 2: Initialize request
            print("Testing initialize request...")
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
            
            async with session.post(
                'http://localhost:8080/mcp',
                json=init_request,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert resp.status == 200
                response = await resp.json()
                assert response["jsonrpc"] == "2.0"
                assert response["id"] == 1
                assert "result" in response
                assert response["result"]["serverInfo"]["name"] == "vibecode-feedback-server"
                print("✅ Initialize request test passed")
            
            # Test 3: List tools request
            print("Testing tools/list request...")
            list_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with session.post(
                'http://localhost:8080/mcp',
                json=list_request,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert resp.status == 200
                response = await resp.json()
                assert response["jsonrpc"] == "2.0"
                assert response["id"] == 2
                assert "result" in response
                assert "tools" in response["result"]
                assert len(response["result"]["tools"]) == 3
                print("✅ List tools request test passed")
            
            # Test 4: Invalid method should return error
            print("Testing error handling...")
            invalid_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "invalid_method",
                "params": {}
            }
            
            async with session.post(
                'http://localhost:8080/mcp',
                json=invalid_request,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert resp.status == 200  # JSON-RPC errors are still HTTP 200
                response = await resp.json()
                assert response["jsonrpc"] == "2.0"
                assert response["id"] == 3
                assert "error" in response
                assert response["error"]["code"] == -32601  # Method not found
                print("✅ Error handling test passed")
            
            # Test 5: CORS headers
            print("Testing CORS headers...")
            async with session.post(
                'http://localhost:8080/mcp',
                json=init_request,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert 'Access-Control-Allow-Origin' in resp.headers
                assert resp.headers['Access-Control-Allow-Origin'] == '*'
                print("✅ CORS headers test passed")
            
        print("\n🎉 All HTTP functionality tests passed!")
        print("The MCP server is working correctly with HTTP transport!")
        
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        raise
    finally:
        # Clean up the server process
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

if __name__ == "__main__":
    asyncio.run(test_http_server())