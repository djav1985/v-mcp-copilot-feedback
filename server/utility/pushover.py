"""Pushover notification utilities."""

from __future__ import annotations

import logging
from typing import Iterable

import requests

from server.utility.config import Config, build_review_url
from server.utility.context_manager import QuestionRecord

logger = logging.getLogger(__name__)

PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json"


def _format_options(options: Iterable[str]) -> str:
    items = [opt.strip() for opt in options if opt and opt.strip()]
    if not items:
        return ""
    formatted = "\n".join(f"• {item}" for item in items)
    return f"Options:\n{formatted}"


def send_question_notification(config: Config, record: QuestionRecord) -> bool:
    """Send a push notification for the question, returning True on success."""

    if not config.pushover_token or not config.pushover_user:
        logger.info("Pushover credentials not configured; skipping notification")
        return False

    review_url = build_review_url(record.auth_key, record.question_id)
    message_lines = [record.question]
    options_block = _format_options(record.preset_answers)
    if options_block:
        message_lines.append(options_block)

    payload = {
        "token": config.pushover_token,
        "user": config.pushover_user,
        "message": "\n\n".join(message_lines),
        "title": "Agent escalation requires your input",
        "url": review_url,
        "url_title": "Answer now",
    }

    try:
        response = requests.post(PUSHOVER_ENDPOINT, data=payload, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - logging path
        logger.error("Failed to send Pushover notification: %s", exc)
        return False

    return True

