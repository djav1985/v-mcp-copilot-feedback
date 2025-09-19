#!/usr/bin/env python3
"""
Test the REST API functionality of the feedback server
"""

import asyncio
import json
import aiohttp
import subprocess
import time
import sys
import os

async def test_rest_api():
    """Test the REST API functionality."""
    print("Testing Feedback Server REST API...")
    
    # Start the server
    server_path = os.path.join(os.path.dirname(__file__), 'feedback_server.py')
    process = subprocess.Popen(
        [sys.executable, server_path, '--host', 'localhost', '--port', '8090'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server time to start
    await asyncio.sleep(3)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Health check
            print("Testing health check endpoint...")
            async with session.get('http://localhost:8090/health') as resp:
                assert resp.status == 200
                health_data = await resp.json()
                assert health_data['status'] == 'healthy'
                assert health_data['service'] == 'vibecode-feedback-server'
                print("✅ Health check test passed")
            
            # Test 2: Ask question endpoint
            print("Testing ask_question endpoint...")
            question_data = {
                "question": "Should we enable feature X for better performance?",
                "preset_answers": ["Yes", "No", "Needs more discussion"]
            }
            
            async with session.post(
                'http://localhost:8090/ask_question',
                json=question_data,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert resp.status == 200
                response = await resp.json()
                assert 'question_id' in response
                assert 'reply_endpoint' in response
                assert response['status'] == 'pending'
                assert response['poll_interval_seconds'] == 30
                
                question_id = response['question_id']
                reply_endpoint = response['reply_endpoint']
                print(f"✅ Ask question test passed, question_id: {question_id}")
            
            # Test 3: Get reply endpoint (should be pending)
            print("Testing get_reply endpoint (pending)...")
            reply_url = f"http://localhost:8090{reply_endpoint}"
            async with session.get(reply_url) as resp:
                assert resp.status == 200
                response = await resp.json()
                assert response['answered'] == False
                assert response['status'] == 'pending'
                assert 'poll_instructions' in response
                print("✅ Get reply (pending) test passed")
            
            # Test 4: Get answer question page (HTML)
            print("Testing answer_question page...")
            # Extract auth_key and question_id from reply_endpoint
            parts = reply_endpoint.split('/')
            auth_key = parts[2]
            question_id = parts[3]
            
            answer_url = f"http://localhost:8090/answer_question/{auth_key}/{question_id}"
            async with session.get(answer_url) as resp:
                assert resp.status == 200
                html_content = await resp.text()
                assert 'Coding Agent Question' in html_content
                assert 'Should we enable feature X' in html_content
                assert 'Yes' in html_content and 'No' in html_content
                print("✅ Answer question page test passed")
            
            # Test 5: Submit answer
            print("Testing answer submission...")
            form_data = aiohttp.FormData()
            form_data.add_field('answer', 'Yes')
            
            async with session.post(answer_url, data=form_data) as resp:
                assert resp.status == 200
                print("✅ Answer submission test passed")
            
            # Test 6: Get reply endpoint (should be answered now)
            print("Testing get_reply endpoint (answered)...")
            async with session.get(reply_url) as resp:
                assert resp.status == 200
                response = await resp.json()
                assert response['answered'] == True
                assert 'reply' in response
                assert response['reply']['answer'] == 'Yes'
                print("✅ Get reply (answered) test passed")
            
            # Test 7: Invalid question ID
            print("Testing invalid auth/question ID...")
            async with session.get('http://localhost:8090/get_reply/invalid/invalid') as resp:
                assert resp.status == 404
                print("✅ Invalid ID handling test passed")
            
            # Test 8: Missing question data
            print("Testing invalid request data...")
            async with session.post(
                'http://localhost:8090/ask_question',
                json={},
                headers={'Content-Type': 'application/json'}
            ) as resp:
                assert resp.status == 400
                print("✅ Invalid request data handling test passed")
            
        print("\n🎉 All REST API tests passed!")
        print("The Feedback Server is working correctly with the new REST API!")
        
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
    asyncio.run(test_rest_api())