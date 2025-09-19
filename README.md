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

2. The server uses only Python standard library, so no additional dependencies are required. Python 3.8+ is required.

## Usage

### Running the Server

Start the MCP server:
```bash
python3 mcp_server.py
```

The server will listen for JSON-RPC requests on stdin and respond on stdout, following the MCP protocol.

### Testing

Run the test suite to verify functionality:
```bash
python3 test_mcp_server.py
```

Run the example demo to see how the server works:
```bash
python3 example_usage.py
```

### Integration with MCP Clients

The server implements the MCP protocol and can be integrated with any MCP-compatible client. Example configuration for popular MCP clients:

#### Claude Desktop
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
- No external dependencies (uses standard library only)

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
