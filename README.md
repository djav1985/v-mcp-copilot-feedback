# MCP Human Handoff Server

This project contains an MCP server that lets coding agents (such as GitHub Copilot agents) escalate
questions to humans for review. The server exposes an MCP tool (`ask_question`) and resource
(`resource://get_reply/{question_id}/{auth_key}`) for the agent while simultaneously serving a secure
Flask web UI for human reviewers. Notifications are delivered through Pushover so that humans can
respond quickly.

The implementation follows the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
and is designed to run locally via Docker Compose or in production with HTTPS enabled.

## Features

* **Agent integration** – Agents call the `ask_question` tool to submit a question and receive
  poll instructions, including an `auth_key` that must be supplied when reading the
  `get_reply` resource.
* **Secure reply polling** – `resource://get_reply/{question_id}/{auth_key}` returns the human
  response once available and gracefully handles expiry after a configurable TTL (5 minutes by
  default).
* **Human review UI** – `/answer_question/<auth_key>/<question_id>` serves a styled HTML form that
  validates credentials, shows preset answers, and accepts custom free-text answers.
* **Pushover notifications** – Each question triggers a push notification that embeds a secure
  review link for the human reviewer.
* **In-memory TTL storage** – Questions and answers are maintained in memory with per-question
  expiry and immutable replies.
* **Configurable TTL overrides** – Individual questions can customize their TTL (including
  zero-second expirations) for tight workflows and testing scenarios.
* **Consistent polling metadata** – Shared helpers keep MCP poll instructions and reply templates
  aligned between tools and resources.

## Project Structure

```
mcp-server/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── CHANGELOG.md
├── README.md
├── server/
│   ├── main.py
│   ├── mcp_server.py
│   ├── flask_server.py
│   ├── requirements.txt
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── ask_question.py
│   │   └── get_reply.py
│   ├── user/
│   │   ├── __init__.py
│   │   ├── answer_form.html
│   │   └── style.css
│   └── utility/
│       ├── __init__.py
│       ├── config.py
│       ├── context_manager.py
│       └── pushover.py
└── test/
    ├── __init__.py
    ├── conftest.py
    ├── test_mcp_server.py
    ├── test_tools.py
    ├── test_user.py
    └── test_utility.py
```

The explicit `server/utility/__init__.py` ensures the module can be imported directly, e.g.
`from server.utility.config import get_config`.

## Configuration

Set the following environment variables. When using Docker Compose, these defaults are
defined inline, but you can override them or provide a `.env` file for local development:

| Variable | Description | Default |
| --- | --- | --- |
| `PUSHOVER_TOKEN` | Application token for Pushover | _unset_ (notifications disabled) |
| `PUSHOVER_USER` | User or group key for Pushover | _unset_ |
| `SERVER_URL` | Base URL used in notification links | `http://localhost:8000` |
| `MCP_API_KEY` | Shared secret that clients must send via the `X-API-Key` header | required |
| `QUESTION_TTL_SECONDS` | TTL before a pending question expires | `300` |
| `POLL_INTERVAL_SECONDS` | Poll frequency hint sent to agents | `30` |
| `FALLBACK_ANSWER` | Reply returned when TTL expires | `Sorry, no human could be reached. Please use your best judgment.` |
| `FLASK_HOST` / `FLASK_PORT` | Bind address and port for the Flask UI | `0.0.0.0` / `8000` |
| `MCP_HOST` / `MCP_PORT` | Bind address and port for the MCP server | `0.0.0.0` / `8765` |
| `MCP_TRANSPORT` | Transport used by `server.run()` (`stdio`, `sse`, or `streamable-http`) | `streamable-http` |

## Local Development

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Provide a `.env` file with the variables above (at minimum `MCP_API_KEY`).

3. Run the Flask and MCP servers together:

   ```bash
   python -m server.main
   ```

   The MCP server listens on `MCP_PORT` while the human review UI is served on `FLASK_PORT`.

4. Run the automated checks:

   ```bash
   ruff check .
   pytest
   ```

## Docker Compose

A ready-to-run Compose file is provided:

```bash
docker compose up --build
```

This launches the MCP transport alongside the Flask UI in a single container. Expose the HTTP
endpoints internally or terminate TLS at an upstream proxy for production deployments. The Compose
file now ships with sensible defaults for every runtime variable, so you can start the stack without
maintaining a separate `.env` file.

## Docker Image Publishing

GitHub Actions automation in [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml)
builds the project image and, when appropriate, pushes it to Docker Hub. The workflow:

* Runs on pull requests targeting `main` or `dev` to ensure Docker changes build cleanly.
* Publishes images for pushes to the `main` and `dev` branches.
* Tags each published image with the branch name (for example, `main` or `dev`) and the commit SHA—no
  rolling `latest` tag is produced.

To enable publishing, configure the following repository secrets with your Docker Hub credentials:

| Secret | Purpose |
| --- | --- |
| `DOCKERHUB_USERNAME` | Docker Hub username or organization name. |
| `DOCKERHUB_TOKEN` | Access token or password with permission to push images. |
| `DOCKERHUB_REPOSITORY` | Target repository in `username/image` format. |

After the secrets are set, pushes to `main` or `dev` automatically update the Docker Hub image. You
can also trigger the workflow manually from the GitHub Actions tab to produce ad-hoc builds from
either branch.

## MCP Workflow Summary

1. **Agent calls `ask_question`** – The tool generates a `question_id` and `auth_key`, stores the
   request with a TTL, triggers a Pushover notification, and tells the agent to poll the
   `get_reply` resource every 30 seconds.
2. **Human answers via Flask UI** – The notification link opens the review page where the human can
   select a preset answer or provide a free-text response.
3. **Agent polls `resource://get_reply/{question_id}/{auth_key}`** – Before an answer arrives, the
   resource returns a pending payload. Once answered, the response is immutable. If the TTL expires
   first, an `"expired"` status is returned with the configured fallback answer.

## Running Tests

```bash
ruff check .
pytest
```

Both commands must succeed before submitting changes.

## License

This project is released under the [MIT License](LICENSE).

