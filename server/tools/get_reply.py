"""Implementation of the `get_reply` MCP resource."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp.server import Context

from server.tools.polling import build_poll_metadata
from server.utility.config import get_config, require_api_key
from server.utility.context_manager import (
    QuestionAccessError,
    QuestionNotFoundError,
    get_question_manager,
)

logger = logging.getLogger(__name__)


def _pending_payload(poll_interval: int) -> dict[str, Any]:
    return {
        "answered": False,
        "status": "pending",
        **build_poll_metadata(poll_interval),
    }


def get_reply(
    question_id: str,
    auth_key: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Return the reply for the requested question if available."""

    require_api_key(ctx)
    config = get_config()
    manager = get_question_manager()

    try:
        record = manager.get_authorized_question_with_ttl(
            question_id=question_id,
            auth_key=auth_key,
            fallback_answer=config.fallback_answer,
        )
    except QuestionNotFoundError as exc:  # pragma: no cover - defensive
        logger.warning("Unknown question_id requested: %s", question_id)
        raise KeyError(f"Unknown question_id: {question_id}") from exc
    except QuestionAccessError as exc:
        logger.warning("Invalid auth key for question %s", question_id)
        raise PermissionError("Invalid auth key") from exc

    now = datetime.now(timezone.utc)
    status = record.status(now)

    if status == "pending":
        return _pending_payload(config.poll_interval_seconds)

    reply_payload = {
        "answered": True,
        "status": status,
        "reply": {"answer": record.answer or config.fallback_answer},
    }

    logger.info("Returning %s reply for question %s", status, record.question_id)
    return reply_payload
