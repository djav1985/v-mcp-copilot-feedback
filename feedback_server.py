#!/usr/bin/env python3
"""
MCP Feedback Server with REST API
Allows coding agents to ask questions and get human feedback via web interface.
"""

import asyncio
import json
import sys
import ssl
import argparse
import time
import secrets
import os
from aiohttp import web, web_request
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import logging
import aiohttp
from datetime import datetime, timedelta

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

class FeedbackServer:
    """REST API Server for Agent-Human Feedback."""
    
    def __init__(self, ttl_seconds: int = 300, pushover_token: str = None, pushover_user: str = None, server_url: str = None):
        self.questions: Dict[str, Question] = {}
        self.ttl_seconds = ttl_seconds
        self.pushover_token = pushover_token
        self.pushover_user = pushover_user
        self.server_url = server_url or "http://localhost:8080"
        
        # Start cleanup task
        asyncio.create_task(self.cleanup_expired_questions())
    
    async def cleanup_expired_questions(self):
        """Periodically clean up expired questions."""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                for question_id, question in self.questions.items():
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
                    del self.questions[key]
                    logger.info(f"Cleaned up old question {key}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
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
            
            data = {
                'token': self.pushover_token,
                'user': self.pushover_user,
                'message': message,
                'title': 'Coding Agent Question',
                'url': answer_url,
                'url_title': 'Answer Question'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.pushover.net/1/messages.json', data=data) as resp:
                    if resp.status == 200:
                        logger.info(f"Pushover notification sent for question {question.question_id}")
                    else:
                        logger.error(f"Failed to send Pushover notification: {resp.status}")
        except Exception as e:
            logger.error(f"Error sending Pushover notification: {e}")
    
    async def ask_question(self, request: web_request.Request) -> web.Response:
        """Handle POST /ask_question from agents."""
        try:
            data = await request.json()
            question_text = data.get('question', '').strip()
            preset_answers = data.get('preset_answers', [])
            
            if not question_text:
                return web.json_response({
                    'error': 'Question text is required'
                }, status=400)
            
            if not isinstance(preset_answers, list):
                return web.json_response({
                    'error': 'preset_answers must be a list'
                }, status=400)
            
            # Generate IDs and create question
            question_id = self.generate_question_id()
            auth_key = self.generate_auth_key()
            
            question = Question(
                question_id=question_id,
                auth_key=auth_key,
                question=question_text,
                preset_answers=preset_answers,
                created_at=time.time(),
                ttl_seconds=self.ttl_seconds
            )
            
            self.questions[question_id] = question
            
            # Send Pushover notification
            await self.send_pushover_notification(question)
            
            reply_endpoint = f"/get_reply/{auth_key}/{question_id}"
            
            return web.json_response({
                'question_id': question_id,
                'status': 'pending',
                'poll_interval_seconds': 30,
                'reply_endpoint': reply_endpoint,
                'poll_instructions': 'Poll this endpoint every 30 seconds for the answer.'
            })
            
        except json.JSONDecodeError:
            return web.json_response({
                'error': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)
    
    async def get_reply(self, request: web_request.Request) -> web.Response:
        """Handle GET /get_reply/{auth_key}/{question_id} for agents polling."""
        try:
            auth_key = request.match_info['auth_key']
            question_id = request.match_info['question_id']
            
            question = self.questions.get(question_id)
            if not question or question.auth_key != auth_key:
                return web.json_response({
                    'error': 'Question not found or invalid auth key'
                }, status=404)
            
            reply_endpoint = f"/get_reply/{auth_key}/{question_id}"
            
            if question.answered:
                return web.json_response({
                    'answered': True,
                    'reply': question.reply
                })
            else:
                return web.json_response({
                    'answered': False,
                    'status': 'pending',
                    'poll_interval_seconds': 30,
                    'poll_instructions': 'Poll this endpoint every 30 seconds for the answer.',
                    'reply_endpoint': reply_endpoint
                })
                
        except Exception as e:
            logger.error(f"Error in get_reply: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)
    
    async def answer_question_get(self, request: web_request.Request) -> web.Response:
        """Handle GET /answer_question/{auth_key}/{question_id} - serve HTML form."""
        try:
            auth_key = request.match_info['auth_key']
            question_id = request.match_info['question_id']
            
            question = self.questions.get(question_id)
            if not question or question.auth_key != auth_key:
                return web.Response(text='Question not found or invalid link', status=404)
            
            if question.answered:
                return web.Response(text=f'''
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
                ''', content_type='text/html')
            
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
            
            return web.Response(text=html, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Error in answer_question_get: {e}")
            return web.Response(text='Internal server error', status=500)
    
    async def answer_question_post(self, request: web_request.Request) -> web.Response:
        """Handle POST /answer_question/{auth_key}/{question_id} - process answer submission."""
        try:
            auth_key = request.match_info['auth_key']
            question_id = request.match_info['question_id']
            
            question = self.questions.get(question_id)
            if not question or question.auth_key != auth_key:
                return web.Response(text='Question not found or invalid link', status=404)
            
            if question.answered:
                return web.Response(text='Question already answered', status=400)
            
            # Get form data
            data = await request.post()
            answer = data.get('answer', '').strip()
            
            if not answer:
                return web.Response(text='Answer is required', status=400)
            
            # Mark as answered
            question.answered = True
            question.reply = {'answer': answer}
            
            logger.info(f"Question {question_id} answered: {answer}")
            
            return web.Response(text='Answer submitted successfully', status=200)
            
        except Exception as e:
            logger.error(f"Error in answer_question_post: {e}")
            return web.Response(text='Internal server error', status=500)
    
    async def health_check(self, request: web_request.Request) -> web.Response:
        """Handle health check requests."""
        return web.json_response({
            "status": "healthy",
            "service": "vibecode-feedback-server",
            "version": "2.0.0",
            "questions_count": len(self.questions)
        })

async def main():
    """Main server entry point."""
    parser = argparse.ArgumentParser(description='VibeCode Feedback REST API Server')
    parser.add_argument('--host', default='localhost', 
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port to bind to (default: 8080)')
    parser.add_argument('--cert', help='Path to SSL certificate file (for HTTPS)')
    parser.add_argument('--key', help='Path to SSL private key file (for HTTPS)')
    parser.add_argument('--ttl', type=int, default=300,
                       help='Question TTL in seconds (default: 300)')
    parser.add_argument('--pushover-token', 
                       default=os.getenv('PUSHOVER_TOKEN'),
                       help='Pushover API token')
    parser.add_argument('--pushover-user',
                       default=os.getenv('PUSHOVER_USER'), 
                       help='Pushover user key')
    parser.add_argument('--server-url',
                       default=os.getenv('SERVER_URL', 'http://localhost:8080'),
                       help='Public server URL for links')
    
    args = parser.parse_args()
    
    # Create server instance
    server = FeedbackServer(
        ttl_seconds=args.ttl,
        pushover_token=args.pushover_token,
        pushover_user=args.pushover_user,
        server_url=args.server_url
    )
    
    logger.info("VibeCode Feedback REST API Server starting...")
    
    # Create web app and routes
    app = web.Application()
    
    # Agent-facing endpoints
    app.router.add_post('/ask_question', server.ask_question)
    app.router.add_get('/get_reply/{auth_key}/{question_id}', server.get_reply)
    
    # Human-facing endpoints
    app.router.add_get('/answer_question/{auth_key}/{question_id}', server.answer_question_get)
    app.router.add_post('/answer_question/{auth_key}/{question_id}', server.answer_question_post)
    
    # Health check
    app.router.add_get('/health', server.health_check)
    app.router.add_get('/', server.health_check)
    
    # Create SSL context if certificates provided
    ssl_context = None
    protocol = 'HTTP'
    if args.cert and args.key:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(args.cert, args.key)
        protocol = 'HTTPS'
        logger.info(f"SSL context created with certificate: {args.cert}")
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, args.host, args.port, ssl_context=ssl_context)
    await site.start()
    
    logger.info(f"Feedback Server running on {protocol.lower()}://{args.host}:{args.port}")
    logger.info("Agent endpoints:")
    logger.info(f"  - POST {protocol.lower()}://{args.host}:{args.port}/ask_question")
    logger.info(f"  - GET  {protocol.lower()}://{args.host}:{args.port}/get_reply/{{auth_key}}/{{question_id}}")
    logger.info("Human endpoints:")
    logger.info(f"  - GET/POST {protocol.lower()}://{args.host}:{args.port}/answer_question/{{auth_key}}/{{question_id}}")
    logger.info("Health check:")
    logger.info(f"  - GET {protocol.lower()}://{args.host}:{args.port}/health")
    
    if not args.pushover_token or not args.pushover_user:
        logger.warning("Pushover not configured - set PUSHOVER_TOKEN and PUSHOVER_USER env vars")
    
    # Keep the server running
    try:
        await asyncio.Event().wait()  # Wait forever
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())