from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone

import pytest

from server.tools.ask_question import ask_question
from server.tools.get_reply import get_reply
from server.utility.context_manager import get_question_manager


def test_ask_question_creates_record(monkeypatch: pytest.MonkeyPatch, api_context) -> None:
    captured = {}

    def fake_notify(config, record):
        captured["question_id"] = record.question_id
        return True

    ask_module = importlib.import_module("server.tools.ask_question")
    monkeypatch.setattr(ask_module, "send_question_notification", fake_notify)

    result = ask_question(
        question="Should we enable feature X?",
        preset_answers=["Yes", "No", "Needs more discussion"],
        ctx=api_context(),
    )

    assert result["status"] == "pending"
    assert "question_id" in result
    assert "auth_key" in result
    assert result["poll_interval_seconds"] > 0
    assert captured["question_id"] == result["question_id"]

    record = get_question_manager().get_question(result["question_id"])
    assert record is not None
    assert record.question == "Should we enable feature X?"
    assert record.preset_answers == ["Yes", "No", "Needs more discussion"]


def test_get_reply_lifecycle(monkeypatch: pytest.MonkeyPatch, api_context) -> None:
    ask_module = importlib.import_module("server.tools.ask_question")
    monkeypatch.setattr(ask_module, "send_question_notification", lambda *_: True)
    creation = ask_question("Is release ready?", ["Ship it", "Hold"], ctx=api_context())

    pending = get_reply(
        question_id=creation["question_id"],
        auth_key=creation["auth_key"],
        ctx=api_context(),
    )
    assert pending["status"] == "pending"
    assert pending["answered"] is False

    manager = get_question_manager()
    manager.answer_question(
        question_id=creation["question_id"],
        auth_key=creation["auth_key"],
        answer="Ship it",
        fallback_answer="fallback",
    )

    answered = get_reply(
        question_id=creation["question_id"],
        auth_key=creation["auth_key"],
        ctx=api_context(),
    )
    assert answered["status"] == "answered"
    assert answered["reply"]["answer"] == "Ship it"


def test_get_reply_expired(monkeypatch: pytest.MonkeyPatch, api_context) -> None:
    ask_module = importlib.import_module("server.tools.ask_question")
    monkeypatch.setattr(ask_module, "send_question_notification", lambda *_: True)
    creation = ask_question("Will this expire?", ["Yes"], ctx=api_context())

    manager = get_question_manager()
    record = manager.get_question(creation["question_id"])
    assert record is not None
    record.created_at = datetime.now(timezone.utc) - timedelta(seconds=record.ttl_seconds + 1)

    expired = get_reply(
        question_id=creation["question_id"],
        auth_key=creation["auth_key"],
        ctx=api_context(),
    )
    assert expired["status"] == "expired"
    assert expired["reply"]["answer"].startswith("Sorry")


def test_invalid_api_key_rejected(monkeypatch: pytest.MonkeyPatch, api_context) -> None:
    ask_module = importlib.import_module("server.tools.ask_question")
    monkeypatch.setattr(ask_module, "send_question_notification", lambda *_: True)

    with pytest.raises(PermissionError):
        ask_question("Test question", ctx=api_context(api_key="wrong"))

    creation = ask_question("Another question", ctx=api_context())

    with pytest.raises(PermissionError):
        get_reply(
            question_id=creation["question_id"],
            auth_key=creation["auth_key"],
            ctx=api_context(api_key="invalid"),
        )

