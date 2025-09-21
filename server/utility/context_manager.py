"""In-memory storage for MCP questions and replies."""

from __future__ import annotations

import secrets
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from server.utility.config import DEFAULT_TTL_SECONDS, get_config


class QuestionNotFoundError(KeyError):
    """Raised when a question identifier cannot be located."""


class QuestionAccessError(PermissionError):
    """Raised when an auth key does not match the stored record."""


@dataclass
class QuestionRecord:
    """In-memory representation of a pending question."""

    question_id: str
    auth_key: str
    question: str
    preset_answers: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    answer: str | None = None
    answered_at: datetime | None = None
    expired: bool = False

    def is_answered(self) -> bool:
        return self.answer is not None

    def has_expired(self, now: datetime) -> bool:
        deadline = self.created_at + timedelta(seconds=self.ttl_seconds)
        return now >= deadline

    def status(self, now: datetime) -> str:
        if self.expired:
            return "expired"
        if self.is_answered():
            return "answered"
        if self.has_expired(now):
            return "expired"
        return "pending"

    def mark_answer(self, answer: str, now: datetime) -> None:
        if self.is_answered():
            return
        self.answer = answer
        self.answered_at = now

    def mark_expired(self, fallback_answer: str, now: datetime) -> None:
        if self.is_answered():
            return
        self.answer = fallback_answer
        self.answered_at = now
        self.expired = True


class QuestionContextManager:
    """Manage pending questions and associated replies."""

    def __init__(self, default_ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._default_ttl_seconds = default_ttl_seconds
        self._records: Dict[str, QuestionRecord] = {}
        self._lock = threading.RLock()

    @property
    def default_ttl_seconds(self) -> int:
        return self._default_ttl_seconds

    def set_default_ttl(self, ttl_seconds: int) -> None:
        self._default_ttl_seconds = ttl_seconds

    def create_question(
        self,
        question: str,
        preset_answers: List[str] | None = None,
        ttl_seconds: int | None = None,
    ) -> QuestionRecord:
        """Persist a new question and return the created record."""

        record = QuestionRecord(
            question_id=uuid.uuid4().hex,
            auth_key=secrets.token_urlsafe(32),
            question=question,
            preset_answers=list(preset_answers or []),
            ttl_seconds=ttl_seconds or self._default_ttl_seconds,
        )
        with self._lock:
            self._records[record.question_id] = record
        return record

    def get_question(self, question_id: str) -> QuestionRecord | None:
        with self._lock:
            return self._records.get(question_id)

    def require_question(self, question_id: str) -> QuestionRecord:
        record = self.get_question(question_id)
        if record is None:
            raise QuestionNotFoundError(question_id)
        return record

    def require_authorized_question(self, question_id: str, auth_key: str) -> QuestionRecord:
        record = self.require_question(question_id)
        if record.auth_key != auth_key:
            raise QuestionAccessError("Auth key does not match the stored record")
        return record

    def ensure_ttl_state(
        self,
        record: QuestionRecord,
        fallback_answer: str,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(timezone.utc)
        if not record.expired and not record.is_answered() and record.has_expired(now):
            record.mark_expired(fallback_answer, now)

    def answer_question(
        self,
        question_id: str,
        auth_key: str,
        answer: str,
        fallback_answer: str,
        now: datetime | None = None,
    ) -> QuestionRecord:
        now = now or datetime.now(timezone.utc)
        with self._lock:
            record = self.require_authorized_question(question_id, auth_key)
            self.ensure_ttl_state(record, fallback_answer, now)
            if not record.expired and not record.is_answered():
                record.mark_answer(answer, now)
            return record

    def get_authorized_question_with_ttl(
        self,
        question_id: str,
        auth_key: str,
        fallback_answer: str,
        now: datetime | None = None,
    ) -> QuestionRecord:
        """Return the authorized record after applying TTL rules."""

        now = now or datetime.now(timezone.utc)
        with self._lock:
            record = self.require_authorized_question(question_id, auth_key)
            self.ensure_ttl_state(record, fallback_answer, now)
            return record

    def purge_question(self, question_id: str) -> None:
        with self._lock:
            self._records.pop(question_id, None)


_default_manager: QuestionContextManager | None = None


def get_question_manager() -> QuestionContextManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = QuestionContextManager(get_config().question_ttl_seconds)
    return _default_manager


def set_question_manager(manager: QuestionContextManager) -> None:
    global _default_manager
    _default_manager = manager

