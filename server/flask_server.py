"""Flask application that exposes the human review UI."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, Response, abort, render_template, request, send_from_directory

from server.utility.config import get_config
from server.utility.context_manager import get_question_manager

TEMPLATE_PATH = Path(__file__).resolve().parent / "user"

app = Flask(__name__, template_folder=str(TEMPLATE_PATH), static_folder=None)


@app.route("/")
def healthcheck() -> tuple[str, int]:
    """Basic health endpoint to confirm the server is running."""

    return "MCP human handoff server is running", 200


@app.route("/static/<path:filename>")
def static_assets(filename: str) -> Response:
    """Serve static assets bundled with the Flask UI."""

    return send_from_directory(TEMPLATE_PATH, filename)


@app.route("/answer_question/<auth_key>/<question_id>", methods=["GET", "POST"])
def answer_question(auth_key: str, question_id: str) -> Any:
    manager = get_question_manager()
    config = get_config()

    try:
        record = manager.get_authorized_question_with_ttl(
            question_id=question_id,
            auth_key=auth_key,
            fallback_answer=config.fallback_answer,
        )
    except Exception:  # pragma: no cover - defensive branch
        abort(404)

    status = record.status(datetime.now(timezone.utc))

    if status == "expired":
        return render_template(
            "answer_form.html",
            record=record,
            status=status,
            message="This request has expired and can no longer be answered.",
        )

    error: str | None = None
    submitted = False

    if request.method == "POST":
        selected_answer = request.form.get("selected_answer")
        custom_answer = request.form.get("custom_answer", "").strip()

        if custom_answer:
            chosen_answer = custom_answer
        elif selected_answer:
            chosen_answer = selected_answer
        else:
            error = "Please choose a preset answer or provide a custom response."
            return render_template(
                "answer_form.html",
                record=record,
                status=status,
                error=error,
            )

        record = manager.answer_question(
            question_id=question_id,
            auth_key=auth_key,
            answer=chosen_answer.strip(),
            fallback_answer=config.fallback_answer,
        )
        submitted = True
        status = record.status(datetime.now(timezone.utc))

    return render_template(
        "answer_form.html",
        record=record,
        status=status,
        error=error,
        submitted=submitted,
    )

