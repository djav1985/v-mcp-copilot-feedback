# v-mcp-vibecode-feedback

REST API server that enables coding agents (such as GitHub Copilot agent) to hand off questions to humans for review and decision-making. Features secure question-answering workflow with Pushover notifications and web-based responses.

---

## Features & Workflow

### 1. Agent-Facing API Endpoints

#### POST `/ask_question`
- **Purpose:** Agent submits a question for human review.
- **Request Body:**
  ```json
  {
    "question": "Should we enable feature X?",
    "preset_answers": ["Yes", "No", "Needs more discussion"]
  }
  ```
- **Server Actions:**
  - Generates a secure `question_id` and unique `auth_key` for authentication.
  - Stores the question and answer options in memory with a TTL (default 5 minutes).
  - Responds to the agent with:
    ```json
    {
      "question_id": "abcd1234questionid",
      "status": "pending",
      "poll_interval_seconds": 30,
      "reply_endpoint": "/get_reply/auth_key/question_id",
      "poll_instructions": "Poll this endpoint every 30 seconds for the answer."
    }
    ```
  - Sends a Pushover notification to the human reviewer containing the review link:
    ```
    New question from coding agent:
    Should we enable feature X?
    
    Click to answer: https://your-server/answer_question/auth_key/question_id
    ```

#### GET `/get_reply/{auth_key}/{question_id}`
- **Purpose:** Agent polls for the human's reply, including the `auth_key` for authorization.
- **Polling:** Agent should poll this endpoint every **30 seconds** as instructed in the response.
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
  - If TTL (default 5 minutes) expires with no human answer, replies with:
    ```json
    {
      "answered": true,
      "reply": {
        "answer": "Sorry, no human could be reached. Please use your best judgment.",
        "expired": true
      }
    }
    ```
  - Once answered, the reply is immutable and always returned.

---

### 2. Human-Facing Endpoints (Not Advertised by API)

#### GET `/answer_question/{auth_key}/{question_id}`
- **Purpose:** Serves an HTML web page to the human reviewer for answering.
- **Features:**
  - Displays:
    - Full question text
    - All preset answers, each with a radio button
    - Free-text field for a custom answer
  - The URL (with `auth_key` and `question_id`) is sent via Pushover for secure access.

#### POST `/answer_question/{auth_key}/{question_id}`
- **Purpose:** Handles submission of the human's answer.
- **Request:** Form data including chosen answer.
- **Actions:**
  - Marks the question as answered and stores the reply.
  - After submission, `/get_reply/{auth_key}/{question_id}` will return the answer for the agent.

---

### 3. Security & Expiry

- The `auth_key` is randomly generated per question, ensuring only the notified human or authorized agent can access the reply.
- **Default TTL is 5 minutes.** If not answered in time, the reply will be set to a default message for the agent.
- Questions expire automatically after TTL, and expired questions are cleaned up.
- Once answered, the reply cannot be changed and is always returned for future agent polls.

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

### Method 2: Direct Python

1. **Clone the repository:**
   ```bash
   git clone https://github.com/djav1985/v-mcp-vibecode-feedback.git
   cd v-mcp-vibecode-feedback
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export PUSHOVER_TOKEN="your_pushover_app_token"
   export PUSHOVER_USER="your_pushover_user_key"  
   export SERVER_URL="https://your-domain.com"
   ```

4. **Run the server:**
   ```bash
   python3 feedback_server.py --host 0.0.0.0 --port 8080
   ```

---

## Usage Examples

### Agent Workflow

**1. POST `/ask_question`**
```bash
curl -X POST http://localhost:8080/ask_question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should we enable feature X?",
    "preset_answers": ["Yes", "No", "Needs more discussion"]
  }'
```

**Response:**
```json
{
  "question_id": "abcd1234questionid",
  "status": "pending",
  "poll_interval_seconds": 30,
  "reply_endpoint": "/get_reply/random_auth_key/abcd1234questionid",
  "poll_instructions": "Poll this endpoint every 30 seconds for the answer."
}
```

**2. GET `/get_reply/{auth_key}/{question_id}` (Polling)**
```bash
curl http://localhost:8080/get_reply/random_auth_key/abcd1234questionid
```

**Before answer:**
```json
{
  "answered": false,
  "status": "pending",
  "poll_interval_seconds": 30,
  "poll_instructions": "Poll this endpoint every 30 seconds for the answer."
}
```

**After answer:**
```json
{
  "answered": true,
  "reply": {"answer": "Yes"}
}
```

**After TTL expires (no human answer):**
```json
{
  "answered": true,
  "reply": {
    "answer": "Sorry, no human could be reached. Please use your best judgment.",
    "expired": true
  }
}
```

### Human Workflow

1. **Receives Pushover notification** with secure link
2. **Clicks link** to open web form
3. **Selects preset answer or types custom response**
4. **Submits answer** via web form
5. **Agent retrieves answer** through polling endpoint

---

## Configuration

### Command Line Options

```bash
python3 feedback_server.py --help
```

- `--host HOST`: Host to bind to (default: localhost)
- `--port PORT`: Port to bind to (default: 8080)
- `--cert CERT`: Path to SSL certificate file (for HTTPS)
- `--key KEY`: Path to SSL private key file (for HTTPS)
- `--ttl TTL`: Question TTL in seconds (default: 300)
- `--pushover-token TOKEN`: Pushover API token
- `--pushover-user USER`: Pushover user key
- `--server-url URL`: Public server URL for links

### Environment Variables

- `PUSHOVER_TOKEN`: Pushover application token
- `PUSHOVER_USER`: Pushover user key
- `SERVER_URL`: Public URL where the server is accessible
- `PORT`: Server port (default: 8080)
- `HOST`: Server host (default: localhost)

### HTTPS Setup

For HTTPS support, provide SSL certificate files:

```bash
python3 feedback_server.py --cert /path/to/cert.pem --key /path/to/key.pem
```

Or mount certificates in Docker:
```bash
# Place certificates in ./certs/ directory
docker-compose up
```

---

## Testing

Run the comprehensive test suite:

```bash
python3 test_rest_api.py
```

This tests:
- Health check endpoint
- Question submission
- Answer polling
- Web interface
- Answer submission
- Error handling
- Security validation

---

## API Reference

### Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/health` | Health check | No |
| POST | `/ask_question` | Submit question | No |
| GET | `/get_reply/{auth_key}/{question_id}` | Poll for answer | Yes (auth_key) |
| GET | `/answer_question/{auth_key}/{question_id}` | Human answer form | Yes (auth_key) |
| POST | `/answer_question/{auth_key}/{question_id}` | Submit human answer | Yes (auth_key) |

### Security Features

- **Secure random auth keys** for each question
- **TTL-based expiration** with automatic cleanup
- **Immutable answers** once submitted
- **Input validation** on all endpoints
- **HTTPS support** with SSL certificates

---

## Architecture Benefits

This architecture allows agents (e.g., Copilot) to:
- **Hand off questions** to humans for review and input
- **Notify humans instantly** via Pushover
- **Collect structured or custom answers** via secure web form
- **Reliably retrieve answers** through polling
- **Ensure answers are securely submitted** and immutable once complete
- **Provide fallback/default reply** if no human responds in time
- **Secure all access** to replies with `auth_key`

---

## Notes

- All agent-facing endpoints are documented and discoverable
- Human-facing endpoints are only accessible via secure links sent directly to reviewers
- The design supports stateless, reliable polling for seamless agent-human handoff
- Fallback handling ensures agents never get stuck waiting indefinitely
- Docker support provides easy deployment and scaling

---

## Requirements

- Python 3.8 or higher
- aiohttp>=3.8.0 (HTTP server framework)
- Pushover account and API token (for notifications)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.