"""Configuration helpers for the MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_TTL_SECONDS = 300
DEFAULT_POLL_INTERVAL = 30
DEFAULT_FALLBACK = "Sorry, no human could be reached. Please use your best judgment."


@dataclass
class Config:
    """Runtime configuration derived from environment variables."""

    pushover_token: str | None
    pushover_user: str | None
    server_url: str
    mcp_api_key: str
    question_ttl_seconds: int = DEFAULT_TTL_SECONDS
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL
    fallback_answer: str = DEFAULT_FALLBACK
    flask_host: str = "0.0.0.0"
    flask_port: int = 8000
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8765
    mcp_transport: str = "streamable-http"


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load configuration from the environment (cached)."""

    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_user = os.getenv("PUSHOVER_USER")
    server_url = os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/")
    api_key = os.getenv("MCP_API_KEY", "")
    
    # Safe integer parsing with fallbacks
    try:
        ttl = int(os.getenv("QUESTION_TTL_SECONDS", str(DEFAULT_TTL_SECONDS)))
    except ValueError:
        ttl = DEFAULT_TTL_SECONDS
    
    try:
        poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", str(DEFAULT_POLL_INTERVAL)))
    except ValueError:
        poll_interval = DEFAULT_POLL_INTERVAL
    
    fallback_answer = os.getenv("FALLBACK_ANSWER", DEFAULT_FALLBACK)
    flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
    
    try:
        flask_port = int(os.getenv("FLASK_PORT", "8000"))
    except ValueError:
        flask_port = 8000
        
    mcp_host = os.getenv("MCP_HOST", "0.0.0.0")
    
    try:
        mcp_port = int(os.getenv("MCP_PORT", "8765"))
    except ValueError:
        mcp_port = 8765
        
    mcp_transport = os.getenv("MCP_TRANSPORT", "streamable-http")

    return Config(
        pushover_token=pushover_token,
        pushover_user=pushover_user,
        server_url=server_url,
        mcp_api_key=api_key,
        question_ttl_seconds=ttl,
        poll_interval_seconds=poll_interval,
        fallback_answer=fallback_answer,
        flask_host=flask_host,
        flask_port=flask_port,
        mcp_host=mcp_host,
        mcp_port=mcp_port,
        mcp_transport=mcp_transport,
    )


def reset_config_cache() -> None:
    """Clear the cached configuration (useful for tests)."""

    get_config.cache_clear()


def build_review_url(auth_key: str, question_id: str) -> str:
    """Return the fully qualified review URL for a question."""

    config = get_config()
    return f"{config.server_url}/answer_question/{auth_key}/{question_id}"


def _extract_header(headers: Any, name: str) -> str | None:
    """Read a header from common mapping types."""

    if headers is None:
        return None

    if hasattr(headers, "get"):
        try:
            return headers.get(name)  # type: ignore[no-any-return]
        except TypeError:
            return None

    return None


def extract_api_key_from_context(ctx: Any | None) -> str | None:
    """Retrieve the X-API-Key header from an MCP request context."""

    if ctx is None:
        return None

    request_context = getattr(ctx, "request_context", None)
    if request_context is None:
        return None

    request = getattr(request_context, "request", None)
    if request is None:
        return None

    headers = getattr(request, "headers", None)
    if headers is None and isinstance(request, dict):
        headers = request.get("headers")

    if headers is None:
        return None

    # Try both possible header name variations
    return _extract_header(headers, "X-API-Key") or _extract_header(headers, "x-api-key")


def require_api_key(ctx: Any | None, provided_key: str | None = None) -> None:
    """Validate that the supplied API key matches the configured secret."""

    config = get_config()
    expected = config.mcp_api_key
    if not expected:
        # No API key configured; nothing to enforce.
        return

    candidate = provided_key or extract_api_key_from_context(ctx)
    if candidate != expected:
        raise PermissionError("Invalid or missing X-API-Key header")

