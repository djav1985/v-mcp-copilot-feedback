from __future__ import annotations

from datetime import datetime, timedelta, timezone

from server.flask_server import app
from server.utility.context_manager import get_question_manager


def test_answer_form_get(question_manager) -> None:
    record = question_manager.create_question(
        "Do you approve the rollout?",
        ["Approve", "Reject"],
        ttl_seconds=300,
    )

    with app.test_client() as client:
        response = client.get(
            f"/answer_question/{record.auth_key}/{record.question_id}"
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Do you approve the rollout?" in html
        assert "Approve" in html


def test_answer_form_post_records_reply(question_manager) -> None:
    record = question_manager.create_question("Which option?", ["Option A"], ttl_seconds=300)

    with app.test_client() as client:
        response = client.post(
            f"/answer_question/{record.auth_key}/{record.question_id}",
            data={"selected_answer": "Option A"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Answer submitted" in html

    stored = get_question_manager().get_question(record.question_id)
    assert stored is not None
    assert stored.answer == "Option A"


def test_expired_question_shows_notice(question_manager) -> None:
    record = question_manager.create_question("Will this expire?", ["Yes"], ttl_seconds=1)
    record.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)

    with app.test_client() as client:
        response = client.get(
            f"/answer_question/{record.auth_key}/{record.question_id}"
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "expired" in html.lower()

