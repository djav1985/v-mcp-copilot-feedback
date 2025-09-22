"""Implementation of the `ask_question` MCP tool."""

from __future__ import annotations

import logging
from typing import Any, List

from mcp.server.fastmcp.server import Context

from server.tools.polling import build_poll_metadata
from server.utility.config import get_config, require_api_key
from server.utility.context_manager import get_question_manager
from server.utility.pushover import send_question_notification

logger = logging.getLogger(__name__)


def _sanitize_preset_answers(preset_answers: List[str] | None) -> List[str]:
    cleaned: List[str] = []
    for answer in preset_answers or []:
        if not answer:
            continue
        text = answer.strip()
        if text:
            cleaned.append(text)
    return cleaned


def ask_question(
    question: str,
    preset_answers: List[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Register a question for human review and notify the reviewer."""

    require_api_key(ctx)
    config = get_config()

    if not question or not question.strip():
        raise ValueError("Question text must not be empty")

    manager = get_question_manager()
    record = manager.create_question(
        question=question.strip(),
        preset_answers=_sanitize_preset_answers(preset_answers),
        ttl_seconds=config.question_ttl_seconds,
    )

    notification_sent = send_question_notification(config, record)
    logger.info(
        "Created question %s (notification_sent=%s)",
        record.question_id,
        notification_sent,
    )

    poll_metadata = build_poll_metadata(config.poll_interval_seconds)

    return {
        **poll_metadata,
        "question_id": record.question_id,
        "auth_key": record.auth_key,
        "status": "pending",
        "expires_in_seconds": record.ttl_seconds,
    }
