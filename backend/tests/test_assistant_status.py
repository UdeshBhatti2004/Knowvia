from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.routes import ask as ask_routes
from app.main import app
from app.repositories import workspace_repository

client = TestClient(app)

# conftest's auth bypass makes every request come from workspace "default".
WS = "default"


def _make_workspace():
    workspace_repository._col().insert_one(
        {"_id": WS, "owner_id": "o1", "name": "Shop", "widget_key": "k1"}
    )


def _fake_answer(monkeypatch):
    monkeypatch.setattr(ask_routes, "ensure_loaded", lambda ws: None)
    monkeypatch.setattr(
        ask_routes, "ask_question", lambda request, ws: {"answer": "ok"}
    )


def test_status_is_empty_before_any_test():
    _make_workspace()
    res = client.get("/assistant/status")
    assert res.status_code == 200
    assert res.json() == {"tested_at": None}


def test_successful_ask_records_test_time(monkeypatch):
    _make_workspace()
    _fake_answer(monkeypatch)

    assert client.post("/ask", json={"question": "hi?"}).status_code == 200

    assert client.get("/assistant/status").json()["tested_at"]


def test_failed_ask_does_not_record_test_time(monkeypatch):
    _make_workspace()
    monkeypatch.setattr(ask_routes, "ensure_loaded", lambda ws: None)

    def boom(request, ws):
        raise HTTPException(status_code=502, detail="down")

    monkeypatch.setattr(ask_routes, "ask_question", boom)

    assert client.post("/ask", json={"question": "hi?"}).status_code == 502
    assert client.get("/assistant/status").json() == {"tested_at": None}


def test_recording_failure_never_breaks_ask(monkeypatch):
    _make_workspace()
    _fake_answer(monkeypatch)

    def broken(workspace_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(workspace_repository, "mark_tested", broken)

    assert client.post("/ask", json={"question": "hi?"}).status_code == 200