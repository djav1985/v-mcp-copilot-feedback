from __future__ import annotations

from types import SimpleNamespace
from typing import Callable

import pytest

from server.utility import config as config_module
from server.utility import context_manager as context_module


@pytest.fixture(autouse=True)
def configure_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_URL", "http://localhost:8000")
    monkeypatch.setenv("MCP_API_KEY", "test-key")
    monkeypatch.setenv("QUESTION_TTL_SECONDS", "120")
    config_module.reset_config_cache()
    manager = context_module.QuestionContextManager(default_ttl_seconds=120)
    context_module.set_question_manager(manager)
    yield
    context_module.set_question_manager(context_module.QuestionContextManager(default_ttl_seconds=120))
    config_module.reset_config_cache()


@pytest.fixture
def question_manager() -> context_module.QuestionContextManager:
    return context_module.get_question_manager()


@pytest.fixture
def api_context() -> Callable[[str | None], SimpleNamespace]:
    def _factory(api_key: str | None = "test-key") -> SimpleNamespace:
        headers = {}
        if api_key is not None:
            headers["X-API-Key"] = api_key
        request = SimpleNamespace(headers=headers)
        request_context = SimpleNamespace(request=request)
        return SimpleNamespace(request_context=request_context)

    return _factory

