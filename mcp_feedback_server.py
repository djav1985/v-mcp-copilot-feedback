#!/usr/bin/env python3
"""
MCP Server for VibeCode Feedback using MCP Python SDK
Enables coding agents to hand off questions to humans for review and decision-making.
"""

import asyncio
import json
import os
import secrets
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
)

# HTTP server for human interface
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route
import uvicorn
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Question:
    """Represents a question from an agent."""
    question_id: str
    auth_key: str
    question: str
    preset_answers: List[str]
    created_at: float
    ttl_seconds: int = 300  # 5 minutes default
    answered: bool = False
    reply: Optional[Dict[str, Any]] = None
    expired: bool = False

class VibeCodeFeedbackServer:
    """MCP Server for agent-human feedback with web interface."""
    
    def __init__(self):
        self.questions: Dict[str, Question] = {}
        self.pushover_token = os.getenv('PUSHOVER_TOKEN')
        self.pushover_user = os.getenv('PUSHOVER_USER') 
        self.server_url = os.getenv('SERVER_URL', 'http://localhost:8080')
        self.ttl_seconds = int(os.getenv('TTL_SECONDS', '300'))
        
        # Create MCP server instance
        self.mcp_server = Server("vibecode-feedback-server", version="2.0.0")
        
        # Register MCP tools
        self.setup_mcp_tools()
    
    def setup_mcp_tools(self):
        """Setup MCP tools using the Python SDK."""
        
        @self.mcp_server.call_tool()
        async def ask_question(question: str, preset_answers: List[str]) -> List[TextContent]:
            """Agent submits a question for human review."""
            if not question or not question.strip():
                return [TextContent(type="text", text="Error: Question text is required")]
            
            if not isinstance(preset_answers, list):
                return [TextContent(type="text", text="Error: preset_answers must be a list")]
            
            # Generate IDs and create question
            question_id = self.generate_question_id()
            auth_key = self.generate_auth_key()
            
            question_obj = Question(
                question_id=question_id,
                auth_key=auth_key,
                question=question.strip(),
                preset_answers=preset_answers,
                created_at=time.time(),
                ttl_seconds=self.ttl_seconds
            )
            
            self.questions[question_id] = question_obj
            
            # Send Pushover notification
            await self.send_pushover_notification(question_obj)
            
            reply_endpoint = f"/get_reply/{auth_key}/{question_id}"
            
            response_data = {
                "question_id": question_id,
                "status": "pending",
                "poll_interval_seconds": 30,
                "reply_endpoint": reply_endpoint,
                "poll_instructions": "Poll this endpoint every 30 seconds for the answer."
            }
            
            return [TextContent(type="text", text=json.dumps(response_data))]
        
        @self.mcp_server.call_tool()
        async def get_reply(auth_key: str, question_id: str) -> List[TextContent]:
            """Agent polls for the human's reply."""
            question = self.questions.get(question_id)
            if not question or question.auth_key != auth_key:
                return [TextContent(type="text", text="Error: Question not found or invalid auth key")]
            
            reply_endpoint = f"/get_reply/{auth_key}/{question_id}"
            
            if question.answered:
                response_data = {
                    "answered": True,
                    "reply": question.reply
                }
            else:
                response_data = {
                    "answered": False,
                    "status": "pending",
                    "poll_interval_seconds": 30,
                    "poll_instructions": "Poll this endpoint every 30 seconds for the answer.",
                    "reply_endpoint": reply_endpoint
                }
            
            return [TextContent(type="text", text=json.dumps(response_data))]
        
        # Set tool schemas explicitly
        ask_question.name = "ask_question"
        ask_question.description = "Submit a question for human review"
        ask_question.inputSchema = {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the human"
                },
                "preset_answers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of preset answer options"
                }
            },
            "required": ["question", "preset_answers"]
        }
        
        get_reply.name = "get_reply"  
        get_reply.description = "Poll for the human's reply to a question"
        get_reply.inputSchema = {
            "type": "object",
            "properties": {
                "auth_key": {
                    "type": "string", 
                    "description": "Authentication key for the question"
                },
                "question_id": {
                    "type": "string",
                    "description": "Unique identifier for the question"
                }
            },
            "required": ["auth_key", "question_id"]
        }
    
    def generate_question_id(self) -> str:
        """Generate a unique question ID."""
        return secrets.token_urlsafe(16)
    
    def generate_auth_key(self) -> str:
        """Generate a secure auth key."""
        return secrets.token_urlsafe(32)
    
    async def send_pushover_notification(self, question: Question):
        """Send a Pushover notification to the human reviewer."""
        if not self.pushover_token or not self.pushover_user:
            logger.warning("Pushover not configured, skipping notification")
            return
        
        try:
            answer_url = f"{self.server_url}/answer_question/{question.auth_key}/{question.question_id}"
            message = f"New question from coding agent:\n\n{question.question}\n\nClick to answer: {answer_url}"
            
            # Use httpx for Pushover API call
            async with httpx.AsyncClient() as client:
                data = {
                    'token': self.pushover_token,
                    'user': self.pushover_user,
                    'message': message,
                    'title': 'Coding Agent Question',
                    'url': answer_url,
                    'url_title': 'Answer Question'
                }
                
                response = await client.post('https://api.pushover.net/1/messages.json', data=data)
                if response.status_code == 200:
                    logger.info(f"Pushover notification sent for question {question.question_id}")
                else:
                    logger.error(f"Failed to send Pushover notification: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending Pushover notification: {e}")

# Global server instance
feedback_server = VibeCodeFeedbackServer()

# Human-facing web interface endpoints
async def answer_question_get(request):
    """Serve HTML form for answering questions."""
    try:
        auth_key = request.path_params['auth_key']
        question_id = request.path_params['question_id']
        
        question = feedback_server.questions.get(question_id)
        if not question or question.auth_key != auth_key:
            return HTMLResponse('Question not found or invalid link', status_code=404)
        
        if question.answered:
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Question Already Answered</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .question {{ background: #e8f4fd; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                    .answer {{ background: #d4edda; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Question Already Answered</h1>
                    <div class="question">
                        <strong>Question:</strong><br>
                        {question.question}
                    </div>
                    <div class="answer">
                        <strong>Your Answer:</strong><br>
                        {question.reply.get('answer', 'N/A')}
                    </div>
                    <p>The coding agent has been notified of your response.</p>
                </div>
            </body>
            </html>
            '''
            return HTMLResponse(html)
        
        # Create HTML form
        preset_options = ''
        for i, answer in enumerate(question.preset_answers):
            preset_options += f'''
            <label style="display: block; margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; background: #f9f9f9;">
                <input type="radio" name="answer_type" value="preset" data-answer="{answer}" style="margin-right: 10px;">
                {answer}
            </label>
            '''
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Answer Coding Agent Question</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 700px; 
                    margin: 20px auto; 
                    padding: 20px; 
                    background: #f5f5f5; 
                    line-height: 1.6;
                }}
                .container {{ 
                    background: white; 
                    padding: 30px; 
                    border-radius: 12px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1); 
                }}
                .question {{ 
                    background: #e8f4fd; 
                    padding: 20px; 
                    border-left: 4px solid #007bff;
                    border-radius: 6px; 
                    margin: 20px 0; 
                    font-size: 16px;
                }}
                .answers {{ margin: 20px 0; }}
                .custom-answer {{ 
                    margin-top: 20px; 
                    padding: 15px; 
                    border: 1px solid #ddd; 
                    border-radius: 6px; 
                    background: #fafafa;
                }}
                textarea {{ 
                    width: 100%; 
                    min-height: 80px; 
                    padding: 10px; 
                    border: 1px solid #ccc; 
                    border-radius: 4px; 
                    resize: vertical;
                    font-family: inherit;
                }}
                button {{ 
                    background: #007bff; 
                    color: white; 
                    padding: 12px 25px; 
                    border: none; 
                    border-radius: 6px; 
                    cursor: pointer; 
                    font-size: 16px;
                    margin-top: 20px;
                }}
                button:hover {{ background: #0056b3; }}
                .header {{ color: #333; margin-bottom: 10px; }}
                .instruction {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">🤖 Coding Agent Question</h1>
                <p class="instruction">A coding agent needs your input to make a decision.</p>
                
                <div class="question">
                    <strong>Question:</strong><br>
                    {question.question}
                </div>
                
                <form method="post" id="answerForm">
                    <div class="answers">
                        <h3>Choose your answer:</h3>
                        {preset_options}
                        
                        <div class="custom-answer">
                            <label style="display: block; margin: 10px 0; cursor: pointer;">
                                <input type="radio" name="answer_type" value="custom" style="margin-right: 10px;">
                                <strong>Custom answer:</strong>
                            </label>
                            <textarea name="custom_answer" placeholder="Type your custom answer here..."></textarea>
                        </div>
                    </div>
                    
                    <button type="submit">Submit Answer</button>
                </form>
                
                <script>
                    document.getElementById('answerForm').addEventListener('submit', function(e) {{
                        e.preventDefault();
                        
                        const formData = new FormData();
                        const selectedType = document.querySelector('input[name="answer_type"]:checked');
                        
                        if (!selectedType) {{
                            alert('Please select an answer option.');
                            return;
                        }}
                        
                        if (selectedType.value === 'preset') {{
                            formData.append('answer', selectedType.getAttribute('data-answer'));
                        }} else {{
                            const customAnswer = document.querySelector('textarea[name="custom_answer"]').value.trim();
                            if (!customAnswer) {{
                                alert('Please provide a custom answer.');
                                return;
                            }}
                            formData.append('answer', customAnswer);
                        }}
                        
                        fetch(window.location.href, {{
                            method: 'POST',
                            body: formData
                        }})
                        .then(response => {{
                            if (response.ok) {{
                                document.body.innerHTML = `
                                    <div class="container">
                                        <h1 style="color: #28a745;">✅ Answer Submitted!</h1>
                                        <p>Your answer has been sent to the coding agent. This page can now be closed.</p>
                                    </div>
                                `;
                            }} else {{
                                alert('Error submitting answer. Please try again.');
                            }}
                        }})
                        .catch(error => {{
                            alert('Error submitting answer. Please try again.');
                            console.error('Error:', error);
                        }});
                    }});
                    
                    // Auto-select custom when typing
                    document.querySelector('textarea[name="custom_answer"]').addEventListener('focus', function() {{
                        document.querySelector('input[value="custom"]').checked = true;
                    }});
                </script>
            </div>
        </body>
        </html>
        '''
        
        return HTMLResponse(html)
        
    except Exception as e:
        logger.error(f"Error in answer_question_get: {e}")
        return HTMLResponse('Internal server error', status_code=500)

async def answer_question_post(request):
    """Handle answer submission."""
    try:
        auth_key = request.path_params['auth_key']
        question_id = request.path_params['question_id']
        
        question = feedback_server.questions.get(question_id)
        if not question or question.auth_key != auth_key:
            return Response('Question not found or invalid link', status_code=404)
        
        if question.answered:
            return Response('Question already answered', status_code=400)
        
        # Get form data
        form_data = await request.form()
        answer = form_data.get('answer', '').strip()
        
        if not answer:
            return Response('Answer is required', status_code=400)
        
        # Mark as answered
        question.answered = True
        question.reply = {'answer': answer}
        
        logger.info(f"Question {question_id} answered: {answer}")
        
        return Response('Answer submitted successfully', status_code=200)
        
    except Exception as e:
        logger.error(f"Error in answer_question_post: {e}")
        return Response('Internal server error', status_code=500)

async def health_check(request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "vibecode-feedback-mcp-server",
        "version": "2.0.0",
        "questions_count": len(feedback_server.questions)
    })

# Create Starlette app for human interface
web_app = Starlette(routes=[
    Route('/answer_question/{auth_key}/{question_id}', answer_question_get, methods=["GET"]),
    Route('/answer_question/{auth_key}/{question_id}', answer_question_post, methods=["POST"]),
    Route('/health', health_check),
    Route('/', health_check),
])

async def run_web_server():
    """Run the web server for human interface."""
    port = int(os.getenv('PORT', '8080'))
    host = os.getenv('HOST', '0.0.0.0')
    
    config = uvicorn.Config(
        web_app,
        host=host,
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    logger.info(f"Starting web server on {host}:{port}")
    await server.serve()

async def main():
    """Main entry point - runs both MCP server and web interface."""
    # Start cleanup task
    cleanup_task = asyncio.create_task(cleanup_expired_questions())
    
    # Start web server in background
    web_task = asyncio.create_task(run_web_server())
    
    # Run MCP server on stdio
    logger.info("Starting MCP server on stdio...")
    try:
        async with stdio_server(feedback_server.mcp_server) as (read_stream, write_stream):
            await feedback_server.mcp_server.run(
                read_stream,
                write_stream,
                feedback_server.mcp_server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        cleanup_task.cancel()
        web_task.cancel()

async def cleanup_expired_questions():
    """Periodically clean up expired questions."""
    while True:
        try:
            current_time = time.time()
            expired_keys = []
            
            for question_id, question in feedback_server.questions.items():
                if not question.answered and current_time - question.created_at > question.ttl_seconds:
                    # Mark as expired and set default reply
                    question.expired = True
                    question.answered = True
                    question.reply = {
                        "answer": "Sorry, no human could be reached. Please use your best judgment.",
                        "expired": True
                    }
                    logger.info(f"Question {question_id} expired after {question.ttl_seconds}s")
                elif question.answered and current_time - question.created_at > question.ttl_seconds * 2:
                    # Clean up old answered questions after 2x TTL
                    expired_keys.append(question_id)
            
            for key in expired_keys:
                del feedback_server.questions[key]
                logger.info(f"Cleaned up old question {key}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    asyncio.run(main())