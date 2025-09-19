from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from server.utility import config as config_module
from server.utility.context_manager import QuestionContextManager, QuestionRecord
from server.utility.pushover import PUSHOVER_ENDPOINT, send_question_notification


def test_config_builds_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PUSHOVER_TOKEN", raising=False)
    monkeypatch.delenv("PUSHOVER_USER", raising=False)
    monkeypatch.setenv("SERVER_URL", "http://test-server")
    monkeypatch.setenv("MCP_API_KEY", "secret")
    monkeypatch.setenv("QUESTION_TTL_SECONDS", "200")
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "45")
    config_module.reset_config_cache()

    config = config_module.get_config()
    assert config.server_url == "http://test-server"
    assert config.mcp_api_key == "secret"
    assert config.question_ttl_seconds == 200
    assert config.poll_interval_seconds == 45


def test_build_review_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_URL", "http://localhost:9000")
    config_module.reset_config_cache()
    url = config_module.build_review_url("auth", "question")
    assert url == "http://localhost:9000/answer_question/auth/question"


def test_question_manager_expiration() -> None:
    manager = QuestionContextManager(default_ttl_seconds=1)
    record = manager.create_question("Test?", ["Yes"], ttl_seconds=1)
    record.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    manager.ensure_ttl_state(record, fallback_answer="fallback")
    assert record.expired is True
    assert record.answer == "fallback"


def test_pushover_skipped_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    config = config_module.Config(
        pushover_token=None,
        pushover_user=None,
        server_url="http://localhost",
        mcp_api_key="",
    )
    record = QuestionRecord(
        question_id="abc",
        auth_key="key",
        question="Need answer?",
        preset_answers=["Yes"],
    )
    assert send_question_notification(config, record) is False


def test_pushover_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    def fake_post(url, data=None, timeout=0):
        called["url"] = url
        called["data"] = data

        class _Response:
            def raise_for_status(self):
                return None

        return _Response()

    monkeypatch.setattr("requests.post", fake_post)

    config = config_module.Config(
        pushover_token="token",
        pushover_user="user",
        server_url="http://localhost",
        mcp_api_key="key",
    )
    record = QuestionRecord(
        question_id="xyz",
        auth_key="auth",
        question="Review this?",
        preset_answers=["Yes", "No"],
    )

    assert send_question_notification(config, record) is True
    assert called["url"] == PUSHOVER_ENDPOINT
    assert called["data"]["token"] == "token"
    assert called["data"]["user"] == "user"


def test_extract_api_key_from_context(api_context) -> None:
    ctx = api_context()
    assert config_module.extract_api_key_from_context(ctx) == "test-key"

    ctx_missing = SimpleNamespace(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={}))
    )
    assert config_module.extract_api_key_from_context(ctx_missing) is None

