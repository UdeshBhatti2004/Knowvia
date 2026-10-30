import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import public as public_route
from app.main import app
from app.repositories import assistant_repository, widget_repository
from app.services.rate_limiter import RateLimiter

client = TestClient(app)

FAKE_RESULT = {
    "question": "fees?",
    "answer": "Fees are 500.",
    "source": "fees.pdf",
    "page": 1,
    "similarity": 0.9,
    "sources": [{"source": "fees.pdf", "page": 1, "similarity": 0.9}],
}


@pytest.fixture(autouse=True)
def isolated(tmp_path):
    """Temp settings files and a fresh limiter, so real data is never touched."""
    with (
        patch.object(
            widget_repository, "WIDGET_SETTINGS_FILE", tmp_path / "widget.json"
        ),
        patch.object(
            assistant_repository,
            "ASSISTANT_SETTINGS_FILE",
            tmp_path / "assistant.json",
        ),
        patch.object(public_route, "limiter", RateLimiter([(60, 3)])),
    ):
        yield tmp_path


def widget_key():
    return client.get("/widget").json()["public_key"]


def auth():
    return {"X-Widget-Key": widget_key()}


def test_key_is_created_once_and_persisted(isolated):
    first = widget_key()
    second = widget_key()

    assert first.startswith("wk_")
    assert first == second
    saved = json.loads((isolated / "widget.json").read_text(encoding="utf-8"))
    assert saved["public_key"] == first


def test_public_endpoints_reject_missing_or_wrong_key():
    with patch.object(public_route, "ask_question") as ask:
        for headers in ({}, {"X-Widget-Key": "wk_wrong"}):
            assert client.get("/public/assistant", headers=headers).status_code == 401
            response = client.post(
                "/public/ask", json={"question": "hi"}, headers=headers
            )
            assert response.status_code == 401

    assert ask.call_count == 0


def test_public_assistant_exposes_only_name_and_welcome():
    response = client.get("/public/assistant", headers=auth())

    assert response.status_code == 200
    assert set(response.json()) == {"name", "welcome_message"}


def test_public_ask_returns_answer_and_sources_without_internals():
    with patch.object(public_route, "ask_question", return_value=FAKE_RESULT):
        response = client.post(
            "/public/ask", json={"question": "  fees?  "}, headers=auth()
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Fees are 500.",
        "sources": [{"source": "fees.pdf", "page": 1}],
    }


@pytest.mark.parametrize("question", ["", "   ", "a" * 501])
def test_public_ask_rejects_bad_questions(question):
    with patch.object(public_route, "ask_question") as ask:
        response = client.post(
            "/public/ask", json={"question": question}, headers=auth()
        )

    assert response.status_code == 422
    assert ask.call_count == 0


def test_public_ask_is_rate_limited_per_visitor():
    headers = auth()

    with patch.object(public_route, "ask_question", return_value=FAKE_RESULT):
        codes = [
            client.post("/public/ask", json={"question": "hi"}, headers=headers)
            for _ in range(4)
        ]

    assert [r.status_code for r in codes] == [200, 200, 200, 429]
    assert int(codes[-1].headers["Retry-After"]) >= 1


def test_limiter_allows_blocks_and_recovers():
    limiter = RateLimiter([(60, 2)])

    assert limiter.check("a", now=0) == 0
    assert limiter.check("a", now=1) == 0
    assert limiter.check("a", now=2) > 0
    assert limiter.check("b", now=2) == 0  # other visitors are unaffected
    assert limiter.check("a", now=61) == 0  # window has passed