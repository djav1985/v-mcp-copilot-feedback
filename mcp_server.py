#!/usr/bin/env python3
"""
MCP Server for VibeCode Feedback
Allows coding agents to ask users questions and get feedback.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Tool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPServer:
    """MCP Server for VibeCode Feedback."""
    
    def __init__(self):
        self.tools: List[Tool] = [
            Tool(
                name="ask_user_question",
                description="Ask the user a question and wait for their feedback",
                input_schema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask the user"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context about what you're working on"
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "How urgent this question is",
                            "default": "medium"
                        }
                    },
                    "required": ["question"]
                }
            ),
            Tool(
                name="request_code_review",
                description="Request user review of code changes",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The code to be reviewed"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what the code does"
                        },
                        "concerns": {
                            "type": "string",
                            "description": "Any specific concerns or areas to focus on"
                        }
                    },
                    "required": ["code", "description"]
                }
            ),
            Tool(
                name="get_user_preference",
                description="Get user preferences for coding decisions",
                input_schema={
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "string",
                            "description": "The decision or choice you need guidance on"
                        },
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Available options to choose from"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context about why this decision needs to be made"
                        }
                    },
                    "required": ["decision", "options"]
                }
            )
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return await self.handle_initialize(params, request_id)
            elif method == "tools/list":
                return await self.handle_list_tools(request_id)
            elif method == "tools/call":
                return await self.handle_call_tool(params, request_id)
            else:
                return self.error_response(request_id, -32601, f"Method not found: {method}")
        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self.error_response(request_id, -32603, f"Internal error: {str(e)}")
    
    async def handle_initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle initialization request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "vibecode-feedback-server",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_list_tools(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools_list = []
        for tool in self.tools:
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_list
            }
        }
    
    async def handle_call_tool(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "ask_user_question":
            return await self.ask_user_question(arguments, request_id)
        elif tool_name == "request_code_review":
            return await self.request_code_review(arguments, request_id)
        elif tool_name == "get_user_preference":
            return await self.get_user_preference(arguments, request_id)
        else:
            return self.error_response(request_id, -32602, f"Unknown tool: {tool_name}")
    
    async def ask_user_question(self, args: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Ask the user a question."""
        question = args.get("question", "")
        context = args.get("context", "")
        urgency = args.get("urgency", "medium")
        
        # Format the question for display
        formatted_question = f"\n{'='*50}\n"
        formatted_question += f"QUESTION ({urgency.upper()} PRIORITY)\n"
        formatted_question += f"{'='*50}\n"
        if context:
            formatted_question += f"Context: {context}\n\n"
        formatted_question += f"Question: {question}\n"
        formatted_question += f"{'='*50}\n"
        formatted_question += "Please provide your response: "
        
        # Get user input
        print(formatted_question, end="")
        sys.stdout.flush()
        
        try:
            user_response = input()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"User response: {user_response}"
                        }
                    ]
                }
            }
        except (EOFError, KeyboardInterrupt):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "User did not provide a response (input interrupted)"
                        }
                    ]
                }
            }
    
    async def request_code_review(self, args: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Request code review from user."""
        code = args.get("code", "")
        description = args.get("description", "")
        concerns = args.get("concerns", "")
        
        # Format the code review request
        review_request = f"\n{'='*60}\n"
        review_request += f"CODE REVIEW REQUEST\n"
        review_request += f"{'='*60}\n"
        review_request += f"Description: {description}\n\n"
        if concerns:
            review_request += f"Specific concerns: {concerns}\n\n"
        review_request += f"Code to review:\n"
        review_request += f"{'-'*40}\n"
        review_request += f"{code}\n"
        review_request += f"{'-'*40}\n"
        review_request += f"Please provide your review comments: "
        
        print(review_request, end="")
        sys.stdout.flush()
        
        try:
            user_review = input()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Code review feedback: {user_review}"
                        }
                    ]
                }
            }
        except (EOFError, KeyboardInterrupt):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "User did not provide review feedback (input interrupted)"
                        }
                    ]
                }
            }
    
    async def get_user_preference(self, args: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Get user preference for a decision."""
        decision = args.get("decision", "")
        options = args.get("options", [])
        context = args.get("context", "")
        
        # Format the preference request
        pref_request = f"\n{'='*50}\n"
        pref_request += f"PREFERENCE REQUEST\n"
        pref_request += f"{'='*50}\n"
        pref_request += f"Decision needed: {decision}\n\n"
        if context:
            pref_request += f"Context: {context}\n\n"
        pref_request += f"Available options:\n"
        for i, option in enumerate(options, 1):
            pref_request += f"  {i}. {option}\n"
        pref_request += f"\nPlease choose an option (number or description): "
        
        print(pref_request, end="")
        sys.stdout.flush()
        
        try:
            user_choice = input()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"User preference: {user_choice}"
                        }
                    ]
                }
            }
        except (EOFError, KeyboardInterrupt):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "User did not provide preference (input interrupted)"
                        }
                    ]
                }
            }
    
    def error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

async def main():
    """Main server loop."""
    server = MCPServer()
    logger.info("VibeCode Feedback MCP Server starting...")
    
    # Read from stdin and write to stdout for MCP communication
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = await server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = server.error_response(None, -32700, "Parse error")
                print(json.dumps(error_response))
                sys.stdout.flush()
                
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main())