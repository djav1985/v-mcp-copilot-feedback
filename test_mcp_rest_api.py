#!/usr/bin/env python3
"""
Test the MCP-SDK based REST API server implementation
"""

import asyncio
import json
import subprocess
import time
import sys
import os
import httpx

async def test_rest_api_with_mcp_sdk():
    """Test the REST API functionality built with MCP SDK foundation."""
    print("Testing MCP-SDK based REST API Server...")
    
    # Start the server
    server_path = os.path.join(os.path.dirname(__file__), 'mcp_feedback_server.py')
    server_env = os.environ.copy()
    server_env['PORT'] = '8091'
    server_env['HOST'] = 'localhost'
    
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=server_env
    )
    
    # Give the server time to start
    await asyncio.sleep(3)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Health check
            print("Testing health check endpoint...")
            response = await client.get('http://localhost:8091/health')
            assert response.status_code == 200
            health_data = response.json()
            assert health_data['status'] == 'healthy'
            assert health_data['service'] == 'vibecode-feedback-mcp-server'
            print("✅ Health check test passed")
            
            # Test 2: POST /ask_question endpoint (as specified by user)
            print("Testing POST /ask_question endpoint...")
            question_data = {
                "question": "Should we implement caching for the API responses to improve performance?",
                "preset_answers": ["Yes, implement Redis caching", "No, keep it simple for now", "Yes, but use in-memory caching", "Needs more analysis first"]
            }
            
            response = await client.post(
                'http://localhost:8091/ask_question',
                json=question_data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert 'question_id' in response_data
            assert 'reply_endpoint' in response_data
            assert response_data['status'] == 'pending'
            assert response_data['poll_interval_seconds'] == 30
            assert response_data['poll_instructions'] == 'Poll this endpoint every 30 seconds for the answer.'
            
            question_id = response_data['question_id']
            reply_endpoint = response_data['reply_endpoint']
            print(f"✅ POST /ask_question test passed, question_id: {question_id}")
            
            # Test 3: GET /get_reply endpoint (should be pending)
            print("Testing GET /get_reply endpoint (pending)...")
            reply_url = f"http://localhost:8091{reply_endpoint}"
            response = await client.get(reply_url)
            assert response.status_code == 200
            response_data = response.json()
            assert response_data['answered'] == False
            assert response_data['status'] == 'pending'
            assert 'poll_instructions' in response_data
            print("✅ GET /get_reply (pending) test passed")
            
            # Test 4: Get answer question page (HTML)
            print("Testing answer_question page...")
            # Extract auth_key and question_id from reply_endpoint
            parts = reply_endpoint.split('/')
            auth_key = parts[2]
            question_id = parts[3]
            
            answer_url = f"http://localhost:8091/answer_question/{auth_key}/{question_id}"
            response = await client.get(answer_url)
            assert response.status_code == 200
            html_content = response.text
            assert 'Coding Agent Question' in html_content
            assert 'Should we implement caching' in html_content
            assert 'Redis caching' in html_content
            print("✅ Answer question page test passed")
            
            # Test 5: Submit answer
            print("Testing answer submission...")
            form_data = {'answer': 'Yes, implement Redis caching'}
            response = await client.post(answer_url, data=form_data)
            assert response.status_code == 200
            print("✅ Answer submission test passed")
            
            # Test 6: GET /get_reply endpoint (should be answered now)
            print("Testing GET /get_reply endpoint (answered)...")
            response = await client.get(reply_url)
            assert response.status_code == 200
            response_data = response.json()
            assert response_data['answered'] == True
            assert 'reply' in response_data
            assert response_data['reply']['answer'] == 'Yes, implement Redis caching'
            print("✅ GET /get_reply (answered) test passed")
            
            # Test 7: Invalid auth/question ID
            print("Testing invalid auth/question ID...")
            response = await client.get('http://localhost:8091/get_reply/invalid/invalid')
            assert response.status_code == 404
            print("✅ Invalid ID handling test passed")
            
            # Test 8: Missing question data
            print("Testing invalid request data...")
            response = await client.post(
                'http://localhost:8091/ask_question',
                json={},
                headers={'Content-Type': 'application/json'}
            )
            assert response.status_code == 400
            print("✅ Invalid request data handling test passed")
            
        print("\n🎉 All MCP-SDK based REST API tests passed!")
        print("The server now provides REST API endpoints as specified while being built with MCP SDK!")
        
    except Exception as e:
        print(f"❌ REST API test failed: {e}")
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
    asyncio.run(test_rest_api_with_mcp_sdk())