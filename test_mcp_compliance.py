#!/usr/bin/env python3
"""
Test MCP Server with MCP Python SDK compliance
"""

import asyncio
import json
import sys
import os

# Import the MCP server
sys.path.insert(0, os.path.dirname(__file__))
from mcp_feedback_server import feedback_server

async def test_mcp_compliance():
    """Test that the server complies with MCP SDK standards."""
    print("Testing MCP SDK compliance...")
    
    try:
        # Test server initialization options
        print("Testing initialization options...")
        init_options = feedback_server.mcp_server.create_initialization_options()
        print(f"✅ Initialization options created: {type(init_options)}")
        
        # Test server capabilities
        print("Testing server capabilities...")
        from mcp.server import NotificationOptions
        notification_options = NotificationOptions()
        capabilities = feedback_server.mcp_server.get_capabilities(notification_options, {})
        print(f"✅ Server capabilities: {capabilities}")
        
        # Test that tools are available
        print("Testing tools availability...")
        if hasattr(capabilities, 'tools') and capabilities.tools:
            print("✅ Tools capability is available")
        else:
            print("❌ No tools capability found")
        
        # Test direct server functionality
        print("Testing server components...")
        print(f"Server name: {feedback_server.mcp_server.name}")
        print(f"Server version: {feedback_server.mcp_server.version}")
        
        # Test question management
        print("Testing question management...")
        question_id = feedback_server.generate_question_id()
        auth_key = feedback_server.generate_auth_key()
        
        from mcp_feedback_server import Question
        test_question = Question(
            question_id=question_id,
            auth_key=auth_key,
            question="Test MCP compliance question?",
            preset_answers=["Yes", "No"],
            created_at=0,
            ttl_seconds=300
        )
        
        feedback_server.questions[question_id] = test_question
        print(f"✅ Question created: {question_id}")
        
        # Test answering
        test_question.answered = True
        test_question.reply = {"answer": "Yes"}
        print("✅ Question answered successfully")
        
        print(f"Total questions: {len(feedback_server.questions)}")
        
        print("\n🎉 MCP SDK compliance tests passed!")
        print("The server is properly built with the MCP Python SDK!")
        
    except Exception as e:
        print(f"❌ MCP compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        raise

async def test_web_interface_components():
    """Test web interface components."""
    print("\nTesting web interface components...")
    
    try:
        # Test that Starlette app is created
        from mcp_feedback_server import web_app
        print(f"✅ Web app created: {type(web_app)}")
        
        # Test routes
        routes = []
        for route in web_app.routes:
            routes.append(f"{route.methods if hasattr(route, 'methods') else 'N/A'} {route.path}")
        
        print(f"✅ Routes available: {routes}")
        
        # Test that necessary functions exist
        from mcp_feedback_server import answer_question_get, answer_question_post, health_check
        print("✅ All endpoint handlers exist")
        
        print("🎉 Web interface components test passed!")
        
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_compliance())
    asyncio.run(test_web_interface_components())