#!/usr/bin/env python3
"""
Test the MCP-based feedback server implementation
"""

import asyncio
import json
import subprocess
import time
import sys
import os
import httpx

async def test_mcp_based_server():
    """Test the new MCP-based server functionality."""
    print("Testing MCP-based Feedback Server...")
    
    # Start the web server component (for human interface)
    web_server_env = os.environ.copy()
    web_server_env['PORT'] = '8090'
    web_server_env['HOST'] = 'localhost'
    
    # Start just the web server portion for testing
    server_path = os.path.join(os.path.dirname(__file__), 'mcp_feedback_server.py')
    
    # Create a simple test script that only runs the web server
    test_web_script = '''
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mcp_feedback_server import web_app, feedback_server
import uvicorn

async def main():
    config = uvicorn.Config(web_app, host="localhost", port=8090, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open('/tmp/test_web_server.py', 'w') as f:
        f.write(test_web_script)
    
    process = subprocess.Popen(
        [sys.executable, '/tmp/test_web_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=web_server_env
    )
    
    # Give the server time to start
    await asyncio.sleep(3)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Health check
            print("Testing health check endpoint...")
            response = await client.get('http://localhost:8090/health')
            assert response.status_code == 200
            health_data = response.json()
            assert health_data['status'] == 'healthy'
            assert health_data['service'] == 'vibecode-feedback-mcp-server'
            print("✅ Health check test passed")
            
            # Test 2: Create a question directly (simulating MCP tool call)
            print("Testing question creation...")
            # We'll simulate the question creation by calling the server methods directly
            from mcp_feedback_server import feedback_server
            
            # Create a test question
            question_id = feedback_server.generate_question_id()
            auth_key = feedback_server.generate_auth_key()
            
            from mcp_feedback_server import Question
            test_question = Question(
                question_id=question_id,
                auth_key=auth_key,
                question="Should we implement caching for the API responses?",
                preset_answers=["Yes, implement Redis caching", "No, keep it simple", "Needs more analysis"],
                created_at=time.time(),
                ttl_seconds=300
            )
            
            feedback_server.questions[question_id] = test_question
            print(f"✅ Question created with ID: {question_id}")
            
            # Test 3: Access answer page
            print("Testing answer question page...")
            answer_url = f"http://localhost:8090/answer_question/{auth_key}/{question_id}"
            response = await client.get(answer_url)
            assert response.status_code == 200
            html_content = response.text
            assert 'Coding Agent Question' in html_content
            assert 'Should we implement caching' in html_content
            assert 'Redis caching' in html_content
            print("✅ Answer page test passed")
            
            # Test 4: Submit answer
            print("Testing answer submission...")
            form_data = {'answer': 'Yes, implement Redis caching'}
            response = await client.post(answer_url, data=form_data)
            assert response.status_code == 200
            print("✅ Answer submission test passed")
            
            # Test 5: Verify question is answered
            print("Testing question answered state...")
            assert feedback_server.questions[question_id].answered == True
            assert feedback_server.questions[question_id].reply['answer'] == 'Yes, implement Redis caching'
            print("✅ Question answered state test passed")
            
            # Test 6: Test invalid question access
            print("Testing invalid question access...")
            response = await client.get('http://localhost:8090/answer_question/invalid/invalid')
            assert response.status_code == 404
            print("✅ Invalid question access test passed")
            
        print("\n🎉 All MCP-based server tests passed!")
        print("The MCP Feedback Server is working correctly!")
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
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

async def test_mcp_tools():
    """Test the MCP tool functionality directly."""
    print("\nTesting MCP Tools directly...")
    
    try:
        from mcp_feedback_server import feedback_server
        
        # Test ask_question tool
        print("Testing ask_question tool...")
        # Simulate MCP tool call
        tools = feedback_server.mcp_server._tools
        ask_question_tool = None
        for tool in tools.values():
            if hasattr(tool, 'handler') and tool.handler.__name__ == 'ask_question':
                ask_question_tool = tool
                break
        
        if ask_question_tool:
            # Call the tool handler directly
            result = await ask_question_tool.handler(
                question="Test question from MCP tool?", 
                preset_answers=["Yes", "No", "Maybe"]
            )
            
            assert len(result) > 0
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            assert 'question_id' in response_data
            assert response_data['status'] == 'pending'
            assert response_data['poll_interval_seconds'] == 30
            
            question_id = response_data['question_id']
            auth_key = response_data['reply_endpoint'].split('/')[2]
            
            print(f"✅ Ask question tool test passed, question_id: {question_id}")
            
            # Test get_reply tool
            print("Testing get_reply tool...")
            get_reply_tool = None
            for tool in tools.values():
                if hasattr(tool, 'handler') and tool.handler.__name__ == 'get_reply':
                    get_reply_tool = tool
                    break
            
            if get_reply_tool:
                result = await get_reply_tool.handler(auth_key=auth_key, question_id=question_id)
                assert len(result) > 0
                response_text = result[0].text
                response_data = json.loads(response_text)
                
                assert response_data['answered'] == False
                assert response_data['status'] == 'pending'
                print("✅ Get reply tool test passed")
            else:
                print("❌ get_reply tool not found")
        else:
            print("❌ ask_question tool not found")
        
        print("🎉 MCP Tools tests completed!")
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_mcp_based_server())
    asyncio.run(test_mcp_tools())