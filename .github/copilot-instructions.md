# Copilot Instructions for MCP Human Handoff Server

This guide enables AI coding agents to work productively in this codebase. It covers architecture, workflows, conventions, and integration points unique to this project.

## Architecture Overview
- **Purpose:** Escalate coding agent questions to humans for review via MCP protocol and Flask web UI.
- **Main Components:**
  - `server/main.py`: Entry point, launches both MCP and Flask servers.
  - `server/mcp_server.py`: Implements MCP transport and agent-facing API.
  - `server/flask_server.py`: Hosts the human review UI and answer form.
  - `server/tools/ask_question.py` & `get_reply.py`: MCP tools for agent/human communication.
  - `server/utility/`: Config, context management, and Pushover notification logic.
  - `server/user/`: HTML/CSS for the review UI.
- **Data Flow:**
  1. Agent calls `ask_question` (MCP tool) → stores question, triggers Pushover notification.
  2. Human answers via Flask UI → answer stored immutably.
  3. Agent polls `get_reply` (MCP resource) for response or expiry.

## Developer Workflows
- **Local Development:**
  - Create a venv, install with `pip install -e .[dev]`.
  - Run both servers: `python -m server.main`.
  - Use `.env` for secrets/config (see `README.md`).
- **Testing:**
  - Run `ruff check .` and `pytest` before submitting changes.
  - Tests are in `test/` and cover all major modules.
- **Docker Compose:**
  - Use `docker compose up --build` for local/prod deployment.
  - All runtime variables have sensible defaults; override via `.env` or Compose file.
- **Image Publishing:**
  - Automated via GitHub Actions (`.github/workflows/docker-publish.yml`).
  - Publishes images for `main`/`dev` branches, tagged by branch and commit SHA.

## Project-Specific Conventions
- **MCP API Key:** Required for agent access; set via env or Compose.
- **Question TTL:** Questions expire after 5 minutes (default); fallback answer is configurable.
- **Polling:** Agents should poll every 30 seconds (configurable).
- **Immutability:** Once answered, replies cannot be changed.
- **Module Imports:** Use explicit imports (e.g., `from server.utility.config import get_config`).

## Integration Points
- **MCP Python SDK:** Follows official SDK patterns for tool/resource registration.
- **Pushover:** Used for human notifications; disabled if env vars unset.
- **Flask UI:** Accessible at `/answer_question/<auth_key>/<question_id>`.
- **Docker:** Compose file and Dockerfile support local and production use.

## Key Files & Directories
- `server/main.py`, `server/mcp_server.py`, `server/flask_server.py`: Core logic.
- `server/tools/`, `server/utility/`, `server/user/`: Tooling, config, UI.
- `test/`: Pytest-based tests for all modules.
- `.github/workflows/docker-publish.yml`: CI/CD for Docker images.

---

If any section is unclear or missing important project-specific details, please provide feedback to improve these instructions.