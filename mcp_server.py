#!/usr/bin/env python3
"""
MCP Server for VibeCode Feedback
Allows coding agents to ask users questions and get feedback.
"""

import asyncio
import json
import sys
import ssl
import argparse
from aiohttp import web, web_request
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
    """Main server entry point."""
    parser = argparse.ArgumentParser(description='VibeCode Feedback MCP Server')
    parser.add_argument('--mode', choices=['stdio', 'http', 'https'], default='stdio',
                       help='Server mode: stdio (default), http, or https')
    parser.add_argument('--host', default='localhost', 
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port to bind to (default: 8080)')
    parser.add_argument('--cert', help='Path to SSL certificate file (required for https)')
    parser.add_argument('--key', help='Path to SSL private key file (required for https)')
    
    args = parser.parse_args()
    
    server = MCPServer()
    logger.info("VibeCode Feedback MCP Server starting...")
    
    if args.mode == 'stdio':
        await run_stdio_server(server)
    elif args.mode in ['http', 'https']:
        await run_http_server(server, args)
    
async def run_stdio_server(server: 'MCPServer'):
    """Run the server in stdio mode (original implementation)."""
    logger.info("Running in stdio mode...")
    
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

async def run_http_server(server: 'MCPServer', args):
    """Run the server in HTTP/HTTPS mode."""
    is_https = args.mode == 'https'
    protocol = 'HTTPS' if is_https else 'HTTP'
    
    logger.info(f"Running in {protocol} mode on {args.host}:{args.port}")
    
    if is_https and (not args.cert or not args.key):
        logger.error("SSL certificate and key are required for HTTPS mode")
        sys.exit(1)
    
    app = web.Application()
    app.router.add_post('/mcp', lambda request: handle_http_request(server, request))
    app.router.add_get('/', handle_health_check)
    app.router.add_get('/health', handle_health_check)
    
    # Create SSL context for HTTPS
    ssl_context = None
    if is_https:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(args.cert, args.key)
        logger.info(f"SSL context created with certificate: {args.cert}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, args.host, args.port, ssl_context=ssl_context)
    await site.start()
    
    logger.info(f"MCP Server running on {protocol.lower()}://{args.host}:{args.port}")
    logger.info("Endpoints:")
    logger.info(f"  - POST {protocol.lower()}://{args.host}:{args.port}/mcp (MCP JSON-RPC)")
    logger.info(f"  - GET {protocol.lower()}://{args.host}:{args.port}/health (Health check)")
    
    # Keep the server running
    try:
        await asyncio.Event().wait()  # Wait forever
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        await runner.cleanup()

async def handle_http_request(server: 'MCPServer', request: web_request.Request) -> web.Response:
    """Handle HTTP requests for MCP JSON-RPC."""
    try:
        # Ensure it's a POST request with JSON content
        if request.method != 'POST':
            return web.Response(
                status=405,
                text='Method Not Allowed. Use POST.',
                headers={'Allow': 'POST'}
            )
        
        content_type = request.headers.get('Content-Type', '')
        if not content_type.startswith('application/json'):
            return web.Response(
                status=400,
                text='Bad Request. Content-Type must be application/json.'
            )
        
        # Parse JSON request body
        try:
            json_data = await request.json()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request: {e}")
            return web.Response(
                status=400,
                text=f'Bad Request. Invalid JSON: {str(e)}'
            )
        
        # Handle the MCP request
        response_data = await server.handle_request(json_data)
        
        # Return JSON response
        return web.Response(
            text=json.dumps(response_data),
            content_type='application/json',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
        
    except Exception as e:
        logger.error(f"Error handling HTTP request: {e}")
        error_response = server.error_response(None, -32603, f"Internal server error: {str(e)}")
        return web.Response(
            text=json.dumps(error_response),
            content_type='application/json',
            status=500
        )

async def handle_health_check(request: web_request.Request) -> web.Response:
    """Handle health check requests."""
    return web.Response(
        text=json.dumps({
            "status": "healthy",
            "service": "vibecode-feedback-mcp-server",
            "version": "1.0.0"
        }),
        content_type='application/json'
    )

if __name__ == "__main__":
    asyncio.run(main())