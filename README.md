# v-mcp-vibecode-feedback

MCP Server built with the official MCP Python SDK that enables coding agents (such as GitHub Copilot agent) to hand off questions to humans for review and decision-making. Features secure question-answering workflow with Pushover notifications and web-based responses.

**Built with:** [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) ([PyPI: mcp](https://pypi.org/project/mcp/))

---

## Features & Workflow

### 1. MCP Tools (Built with MCP Python SDK)

#### `ask_question` Tool
- **Purpose:** Agent submits a question for human review.
- **Parameters:**
  ```json
  {
    "question": "Should we enable feature X?",
    "preset_answers": ["Yes", "No", "Needs more discussion"]
  }
  ```
- **Server Actions:**
  - Generates a secure `question_id` and unique `auth_key` for authentication.
  - Stores the question and answer options in memory with a TTL (default 5 minutes).
  - Returns JSON response with polling instructions:
    ```json
    {
      "question_id": "abcd1234questionid",
      "status": "pending", 
      "poll_interval_seconds": 30,
      "reply_endpoint": "/get_reply/auth_key/question_id",
      "poll_instructions": "Poll this endpoint every 30 seconds for the answer."
    }
    ```
  - Sends a Pushover notification to the human reviewer with secure link:
    ```
    New question from coding agent:
    Should we enable feature X?
    
    Click to answer: https://your-server/answer_question/auth_key/question_id
    ```

#### `get_reply` Tool
- **Purpose:** Agent polls for the human's reply using the `auth_key` for authorization.
- **Parameters:**
  ```json
  {
    "auth_key": "secure_auth_key",
    "question_id": "abcd1234questionid"
  }
  ```
- **Polling:** Agent should poll every **30 seconds** as instructed in the response.
- **Response:**
  - Before answer:
    ```json
    {
      "answered": false,
      "status": "pending",
      "poll_interval_seconds": 30,
      "poll_instructions": "Poll this endpoint every 30 seconds for the answer.",
      "reply_endpoint": "/get_reply/auth_key/question_id"
    }
    ```
  - After answer:
    ```json
    {
      "answered": true,
      "reply": {"answer": "Yes"}
    }
    ```
  - If TTL (default 5 minutes) expires with no human answer:
    ```json
    {
      "answered": true,
      "reply": {
        "answer": "Sorry, no human could be reached. Please use your best judgment.",
        "expired": true
      }
    }
    ```

### 2. Human-Facing Web Interface (Starlette/FastAPI-style)

#### GET `/answer_question/{auth_key}/{question_id}`
- **Purpose:** Serves an HTML web page to the human reviewer for answering.
- **Features:**
  - Displays full question text
  - All preset answers as radio buttons
  - Free-text field for custom answers
  - Modern responsive design
  - The URL is sent via Pushover for secure access.

#### POST `/answer_question/{auth_key}/{question_id}`
- **Purpose:** Handles submission of the human's answer.
- **Request:** Form data including chosen answer.
- **Actions:**
  - Marks the question as answered and stores the reply.
  - After submission, `get_reply` tool returns the answer for the agent.

### 3. Security & Expiry

- The `auth_key` is randomly generated per question (32-byte URL-safe token)
- **Default TTL is 5 minutes.** Questions expire with fallback response
- Questions are cleaned up automatically after TTL
- Once answered, replies are immutable and always returned for polling
- All access secured with unique auth keys per question

---

## Installation & Setup

### Method 1: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/djav1985/v-mcp-vibecode-feedback.git
   cd v-mcp-vibecode-feedback
   ```

2. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Pushover credentials and server URL
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

### Method 2: Direct Python with MCP SDK

1. **Clone the repository:**
   ```bash
   git clone https://github.com/djav1985/v-mcp-vibecode-feedback.git
   cd v-mcp-vibecode-feedback
   ```

2. **Install MCP Python SDK and dependencies:**
   ```bash
   pip install mcp pushover uvicorn starlette
   # Or use requirements.txt:
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export PUSHOVER_TOKEN="your_pushover_app_token"
   export PUSHOVER_USER="your_pushover_user_key"  
   export SERVER_URL="https://your-domain.com"
   ```

4. **Run the MCP server:**
   ```bash
   python3 mcp_feedback_server.py
   ```

---

## Usage Examples

### MCP Tool Integration

The server provides MCP tools that can be called by any MCP-compatible client:

**Tool: ask_question**
```json
{
  "name": "ask_question",
  "arguments": {
    "question": "Should we enable feature X for better performance?",
    "preset_answers": ["Yes, implement it", "No, keep simple", "Needs more analysis"]
  }
}
```

**Tool: get_reply**
```json
{
  "name": "get_reply", 
  "arguments": {
    "auth_key": "secure_auth_key_here",
    "question_id": "abcd1234questionid"
  }
}
```

### Docker Deployment

**Environment Variables (.env file):**
```bash
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER=your_pushover_user_key
SERVER_URL=https://your-domain.com
PORT=8080
TTL_SECONDS=300
```

**Run with Docker Compose:**
```bash
docker-compose up --build
```

### MCP Client Integration

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "vibecode-feedback": {
      "command": "python3",
      "args": ["/path/to/mcp_feedback_server.py"]
    }
  }
}
```

---

## Human Workflow

1. **Agent calls `ask_question` tool** with question and preset answers
2. **Server sends Pushover notification** to human with secure link
3. **Human receives notification** and clicks link to open web form
4. **Human selects preset answer or types custom response**
5. **Human submits answer** via responsive web interface
6. **Agent polls `get_reply` tool** every 30 seconds until answered
7. **Agent receives answer** and continues workflow

---

## Architecture (MCP Python SDK Implementation)

### MCP Server Core
- **Built with official MCP Python SDK** (`pip install mcp`)
- **Tool Registration:** Uses `@server.call_tool()` decorators
- **Type Safety:** Proper typing with `TextContent` responses
- **Standards Compliant:** Follows MCP protocol specification exactly

### Web Interface
- **Starlette Framework:** Fast, modern ASGI web framework
- **Uvicorn Server:** Production-ready ASGI server
- **Responsive Design:** Works on all devices and screen sizes
- **Form Handling:** JavaScript-enhanced form submission

### Notifications
- **Pushover Integration:** Instant mobile/desktop notifications
- **Secure Links:** Each question gets unique auth_key in URL
- **Rich Messages:** Includes question text and clickable answer link

### Security Architecture
- **Unique Auth Keys:** 32-byte URL-safe tokens per question
- **TTL Management:** Automatic expiry with fallback responses  
- **Memory Cleanup:** Expired questions cleaned up automatically
- **Input Validation:** All inputs validated and sanitized

---

## Testing

Run the comprehensive test suite:

```bash
# Test MCP SDK compliance
python3 test_mcp_compliance.py

# Test tool functionality  
python3 test_mcp_tools.py
```

**Tests Include:**
- MCP SDK initialization and capabilities
- Tool registration and schema validation
- Question creation and management
- Answer polling and responses
- Web interface components
- Error handling and security validation

---

## Configuration

### Command Line Options

The server runs as an MCP server on stdio by default, with a web interface for human interaction.

### Environment Variables

- `PUSHOVER_TOKEN`: Pushover application token
- `PUSHOVER_USER`: Pushover user key
- `SERVER_URL`: Public URL where the server is accessible
- `PORT`: Web interface port (default: 8080) 
- `HOST`: Web interface host (default: 0.0.0.0)
- `TTL_SECONDS`: Question TTL in seconds (default: 300)

### HTTPS Setup

For HTTPS support in production, use a reverse proxy like nginx or deploy behind a load balancer with SSL termination.

---

## API Reference

### MCP Tools

| Tool | Purpose | Required Args | Response |
|------|---------|---------------|----------|
| `ask_question` | Submit question for human review | `question`, `preset_answers` | JSON with question_id and polling info |
| `get_reply` | Poll for human answer | `auth_key`, `question_id` | JSON with answer or pending status |

### Web Endpoints  

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/health` | Health check | No |
| GET | `/answer_question/{auth_key}/{question_id}` | Human answer form | Yes (auth_key) |
| POST | `/answer_question/{auth_key}/{question_id}` | Submit human answer | Yes (auth_key) |

---

## Requirements

- **Python 3.8+** for asyncio and modern typing
- **MCP Python SDK** (`pip install mcp`) - Official MCP implementation
- **Pushover account** and API token for notifications
- **Web server** capabilities for human interface (Uvicorn/Starlette)

---

## Architecture Benefits

This MCP SDK-based architecture provides:

- **Standards Compliance:** Built with official MCP Python SDK
- **Tool Discoverability:** Proper MCP tool registration and schema
- **Type Safety:** Full typing support with MCP SDK types
- **Reliable Polling:** Stateless 30-second polling intervals  
- **Secure Access:** Unique auth keys and TTL-based expiration
- **Mobile Notifications:** Instant Pushover alerts to humans
- **Responsive Interface:** Modern web UI that works everywhere
- **Production Ready:** Docker support with health checks
- **Error Resilience:** Comprehensive error handling and fallbacks

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.