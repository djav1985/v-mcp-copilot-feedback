#!/usr/bin/env python3
"""
Example usage of the VibeCode Feedback MCP Server
This demonstrates how coding agents can interact with the user.
"""

import json
import sys
import os

# Add the current directory to the path to import mcp_server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import MCPServer
import asyncio

async def demo_interactions():
    """Demonstrate MCP server interactions."""
    server = MCPServer()
    
    print("=== VibeCode Feedback MCP Server Demo ===\n")
    print("This demo shows how coding agents can interact with users through the MCP server.\n")
    
    # Initialize the server
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    
    init_response = await server.handle_request(init_request)
    print("Server initialized successfully!\n")
    
    # Demo 1: Ask a simple question
    print("Demo 1: Asking a simple question")
    question_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "ask_user_question",
            "arguments": {
                "question": "What naming convention would you prefer for the new API endpoints?",
                "context": "Working on a REST API for user management",
                "urgency": "medium"
            }
        }
    }
    
    print("Simulating agent asking a question...")
    print("(In a real scenario, this would wait for user input)")
    print("Request:", json.dumps(question_request, indent=2))
    print()
    
    # Demo 2: Request code review
    print("Demo 2: Requesting code review")
    review_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "request_code_review",
            "arguments": {
                "code": """def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)""",
                "description": "Recursive Fibonacci implementation",
                "concerns": "Performance and potential stack overflow for large numbers"
            }
        }
    }
    
    print("Simulating agent requesting code review...")
    print("Request:", json.dumps(review_request, indent=2))
    print()
    
    # Demo 3: Get user preference
    print("Demo 3: Getting user preference")
    preference_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "get_user_preference",
            "arguments": {
                "decision": "Database choice for the new microservice",
                "options": ["PostgreSQL", "MongoDB", "Redis"],
                "context": "Need to store user sessions and preferences with occasional complex queries"
            }
        }
    }
    
    print("Simulating agent asking for user preference...")
    print("Request:", json.dumps(preference_request, indent=2))
    print()
    
    print("=== End of Demo ===")
    print("\nTo run the actual interactive server, use:")
    print("python3 mcp_server.py")
    print("\nThe server will then listen for JSON-RPC requests on stdin and respond on stdout.")

if __name__ == "__main__":
    asyncio.run(demo_interactions())