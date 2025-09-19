#!/usr/bin/env python3
"""
Test HTTPS functionality of the MCP server
"""

import asyncio
import json
import aiohttp
import subprocess
import time
import sys
import os
import ssl

async def test_https_server():
    """Test the MCP server in HTTPS mode."""
    print("Testing MCP Server HTTPS functionality...")
    
    # Start the server in HTTPS mode
    server_path = os.path.join(os.path.dirname(__file__), 'mcp_server.py')
    cert_path = os.path.join(os.path.dirname(__file__), 'test_cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'test_key.pem')
    
    process = subprocess.Popen(
        [sys.executable, server_path, '--mode', 'https', '--port', '8443', 
         '--cert', cert_path, '--key', key_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server time to start
    await asyncio.sleep(2)
    
    try:
        # Create SSL context that accepts self-signed certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Test 1: Health check over HTTPS
            print("Testing HTTPS health check endpoint...")
            async with session.get('https://localhost:8443/health') as resp:
                assert resp.status == 200
                health_data = await resp.json()
                assert health_data['status'] == 'healthy'
                assert health_data['service'] == 'vibecode-feedback-mcp-server'
                print("✅ HTTPS health check test passed")
            
            # Test 2: Initialize request over HTTPS
            print("Testing HTTPS initialize request...")
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
                'https://localhost:8443/mcp',
                json=init_request,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert resp.status == 200
                response = await resp.json()
                assert response["jsonrpc"] == "2.0"
                assert response["id"] == 1
                assert "result" in response
                assert response["result"]["serverInfo"]["name"] == "vibecode-feedback-server"
                print("✅ HTTPS initialize request test passed")
            
            # Test 3: List tools request over HTTPS
            print("Testing HTTPS tools/list request...")
            list_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with session.post(
                'https://localhost:8443/mcp',
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
                print("✅ HTTPS list tools request test passed")
            
        print("\n🎉 All HTTPS functionality tests passed!")
        print("The MCP server is working correctly with HTTPS transport!")
        
    except Exception as e:
        print(f"❌ HTTPS test failed: {e}")
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
    asyncio.run(test_https_server())