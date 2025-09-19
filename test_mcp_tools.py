#!/usr/bin/env python3
"""
Simple test for MCP tools functionality
"""

import asyncio
import json
import sys
import os

# Import the MCP server
sys.path.insert(0, os.path.dirname(__file__))
from mcp_feedback_server import feedback_server

async def test_mcp_tools():
    """Test MCP tools directly."""
    print("Testing MCP Tools functionality...")
    
    try:
        # Test the tools registration
        tools = feedback_server.mcp_server._tools
        print(f"Registered tools: {list(tools.keys())}")
        
        # Find the ask_question tool
        ask_question_tool = None
        get_reply_tool = None
        
        for tool_name, tool in tools.items():
            if hasattr(tool, 'handler') and tool.handler.__name__ == 'ask_question':
                ask_question_tool = tool
            elif hasattr(tool, 'handler') and tool.handler.__name__ == 'get_reply':
                get_reply_tool = tool
        
        if not ask_question_tool:
            print("❌ ask_question tool not found")
            return
        
        if not get_reply_tool:
            print("❌ get_reply tool not found")
            return
        
        print("✅ Both tools found and registered")
        
        # Test ask_question tool
        print("\nTesting ask_question tool...")
        result = await ask_question_tool.handler(
            question="Should we implement caching for better performance?",
            preset_answers=["Yes, implement Redis", "No, keep simple", "Needs analysis"]
        )
        
        assert len(result) > 0
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        assert 'question_id' in response_data
        assert response_data['status'] == 'pending'
        assert response_data['poll_interval_seconds'] == 30
        
        question_id = response_data['question_id']
        auth_key = response_data['reply_endpoint'].split('/')[2]
        
        print(f"✅ ask_question tool worked! Question ID: {question_id}")
        
        # Test get_reply tool (should be pending)
        print("Testing get_reply tool (pending state)...")
        result = await get_reply_tool.handler(auth_key=auth_key, question_id=question_id)
        
        assert len(result) > 0
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        assert response_data['answered'] == False
        assert response_data['status'] == 'pending'
        print("✅ get_reply tool working (pending state)")
        
        # Simulate answering the question
        print("Simulating question answer...")
        question_obj = feedback_server.questions[question_id]
        question_obj.answered = True
        question_obj.reply = {'answer': 'Yes, implement Redis'}
        
        # Test get_reply tool (answered state)
        print("Testing get_reply tool (answered state)...")
        result = await get_reply_tool.handler(auth_key=auth_key, question_id=question_id)
        
        assert len(result) > 0
        response_text = result[0].text  
        response_data = json.loads(response_text)
        
        assert response_data['answered'] == True
        assert response_data['reply']['answer'] == 'Yes, implement Redis'
        print("✅ get_reply tool working (answered state)")
        
        # Test error cases
        print("Testing error cases...")
        result = await get_reply_tool.handler(auth_key="invalid", question_id="invalid")
        assert len(result) > 0
        response_text = result[0].text
        assert "Error:" in response_text
        print("✅ Error handling working")
        
        print("\n🎉 All MCP tool tests passed!")
        print(f"Total questions in memory: {len(feedback_server.questions)}")
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())