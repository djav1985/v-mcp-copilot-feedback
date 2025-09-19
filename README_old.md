# v-mcp-vibecode-feedback

MCP Server that allows coding agents to ask you questions and get feedback.

## Overview

This MCP (Model Context Protocol) server provides tools for coding agents to interact with users directly, enabling them to:
- Ask questions and get immediate feedback
- Request code reviews
- Get user preferences for coding decisions

## Features

The server provides three main tools:

### 1. Ask User Question (`ask_user_question`)
Allows coding agents to ask users questions and wait for their response.

**Parameters:**
- `question` (required): The question to ask the user
- `context` (optional): Context about what you're working on
- `urgency` (optional): Priority level - "low", "medium", or "high"

### 2. Request Code Review (`request_code_review`)
Enables agents to request user review of code changes.

**Parameters:**
- `code` (required): The code to be reviewed
- `description` (required): Description of what the code does
- `concerns` (optional): Specific concerns or areas to focus on

### 3. Get User Preference (`get_user_preference`)
Gets user preferences for coding decisions.

**Parameters:**
- `decision` (required): The decision needing guidance
- `options` (required): Array of available options
- `context` (optional): Context about why this decision needs to be made

## Installation

1. Clone the repository:
```bash
git clone https://github.com/djav1985/v-mcp-vibecode-feedback.git
cd v-mcp-vibecode-feedback
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

The server requires Python 3.8+ and the aiohttp library for HTTP/HTTPS functionality.

## Usage

### Running the Server

The server supports three modes of operation:

#### 1. stdio Mode (Default - MCP Standard)
Start the MCP server in stdio mode for use with MCP clients:
```bash
python3 mcp_server.py
```

#### 2. HTTP Mode  
Start the server with HTTP transport:
```bash
python3 mcp_server.py --mode http --host localhost --port 8080
```

#### 3. HTTPS Mode
Start the server with HTTPS transport (requires SSL certificate):
```bash
python3 mcp_server.py --mode https --host localhost --port 8443 --cert /path/to/cert.pem --key /path/to/key.pem
```

**Command Line Options:**
- `--mode`: Server mode (`stdio`, `http`, or `https`) - default: `stdio`
- `--host`: Host to bind to - default: `localhost`  
- `--port`: Port to bind to - default: `8080`
- `--cert`: Path to SSL certificate file (required for https mode)
- `--key`: Path to SSL private key file (required for https mode)

**HTTP/HTTPS Endpoints:**
- `POST /mcp`: MCP JSON-RPC endpoint
- `GET /health`: Health check endpoint

### Testing

Run the test suite to verify functionality:

**Test stdio mode:**
```bash
python3 test_mcp_server.py
python3 test_integration.py
```

**Test HTTP mode:**
```bash
python3 test_http_server.py
```

**Test HTTPS mode (requires SSL certificates):**
```bash
# Generate test certificates
openssl req -x509 -newkey rsa:2048 -keyout test_key.pem -out test_cert.pem -days 365 -nodes -subj "/CN=localhost"

# Run HTTPS tests
python3 test_https_server.py
```

Run the example demo to see how the server works:
```bash
python3 example_usage.py
```

### Integration with MCP Clients

The server implements the MCP protocol and can be integrated with any MCP-compatible client.

#### stdio Mode (Standard MCP)
Example configuration for popular MCP clients:

**Claude Desktop**
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "vibecode-feedback": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

#### HTTP/HTTPS Mode
For HTTP/HTTPS integration, clients can send JSON-RPC requests to the server endpoints:

**HTTP Example:**
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

**HTTPS Example:**
```bash
curl -X POST https://localhost:8443/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0.0"}
    }
  }' \
  --insecure
```

#### Generic MCP Client
The server responds to standard MCP methods:
- `initialize`: Initialize the connection
- `tools/list`: List available tools
- `tools/call`: Call a specific tool

## Example Interactions

### Asking a Question
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "ask_user_question",
    "arguments": {
      "question": "What naming convention should I use for the API endpoints?",
      "context": "Building a REST API for user management",
      "urgency": "medium"
    }
  }
}
```

### Requesting Code Review
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "request_code_review",
    "arguments": {
      "code": "def process_data(data):\n    return [item.strip().lower() for item in data]",
      "description": "Function to clean and normalize data",
      "concerns": "Performance with large datasets"
    }
  }
}
```

## Development

### File Structure
- `mcp_server.py`: Main MCP server implementation
- `test_mcp_server.py`: Test suite for the server
- `example_usage.py`: Demo script showing server capabilities
- `requirements.txt`: Python dependencies (none required)
- `pyproject.toml`: Project configuration

### Requirements
- Python 3.8 or higher
- aiohttp>=3.8.0 (for HTTP/HTTPS support)
- SSL certificate and private key (for HTTPS mode)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure functionality
5. Submit a pull request

## Support

For issues, questions, or contributions, please use the GitHub issues page.
