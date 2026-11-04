import pytest
from fastapi.testclient import TestClient

from app.api.routes import public as public_route
from app.api.routes import sources as sources_route
from app.api.routes.public import require_widget_key
from app.main import app
from app.repositories import conversation_repository as repo
from app.repositories.source_repository import save_sources_metadata
from app.services import usage_service

client = TestClient(app)


@pytest.fixture
def widget_workspace():
    app.dependency_overrides[require_widget_key] = lambda: "default"
    yield
    app.dependency_overrides.pop(require_widget_key, None)


def _fake_ask(calls):
    def fake(request, workspace_id):
        calls.append(request.question)
        return {"answer": "hi", "sources": []}

    return fake


def test_public_ask_blocked_at_monthly_limit(monkeypatch, widget_workspace):
    calls = []
    monkeypatch.setattr(public_route, "ask_question", _fake_ask(calls))
    monkeypatch.setattr(public_route, "ensure_loaded", lambda _w: None)
    monkeypatch.setitem(
        usage_service.PLANS["free"], "max_questions_per_month", 1
    )
    repo.log_conversation("default", "earlier", "a", "answered", [])

    res = client.post("/public/ask", json={"question": "hello?"})

    assert res.status_code == 429
    assert "monthly question limit" in res.json()["detail"]
    assert calls == []  # Gemini path never reached


def test_public_ask_allowed_below_limit(monkeypatch, widget_workspace):
    calls = []
    monkeypatch.setattr(public_route, "ask_question", _fake_ask(calls))
    monkeypatch.setattr(public_route, "ensure_loaded", lambda _w: None)
    monkeypatch.setitem(
        usage_service.PLANS["free"], "max_questions_per_month", 5
    )

    res = client.post("/public/ask", json={"question": "hello?"})

    assert res.status_code == 200
    assert calls == ["hello?"]


def test_upload_blocked_at_document_limit(monkeypatch):
    monkeypatch.setattr(sources_route, "ensure_loaded", lambda _w: None)
    monkeypatch.setitem(usage_service.PLANS["free"], "max_documents", 1)
    save_sources_metadata({"a.pdf": {"status": "Processed"}}, "default")

    res = client.post(
        "/sources/upload",
        files={"file": ("b.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert res.status_code == 403
    assert "Free plan limit" in res.json()["detail"]