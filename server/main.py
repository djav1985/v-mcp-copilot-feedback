"""Entrypoint that starts the MCP and Flask servers together."""

from __future__ import annotations

import logging
import threading

from server.flask_server import app
from server.mcp_server import get_mcp_server
from server.utility.config import get_config

logger = logging.getLogger(__name__)


def _run_mcp_server() -> None:
    """Start the MCP server using the configured transport."""
    config = get_config()
    server = get_mcp_server()
    logger.info(
        "Starting MCP server on %s:%s via %s transport",
        config.mcp_host,
        config.mcp_port,
        config.mcp_transport,
    )
    server.run(transport=config.mcp_transport)


def main() -> None:
    """Launch the MCP server in a background thread and then run Flask."""
    thread = threading.Thread(target=_run_mcp_server, daemon=True)
    thread.start()

    config = get_config()
    logger.info(
        "Starting Flask app on %s:%s", config.flask_host, config.flask_port
    )
    app.run(host=config.flask_host, port=config.flask_port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

