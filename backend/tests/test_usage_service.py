import pytest
from fastapi import HTTPException

from app.repositories import conversation_repository as repo
from app.repositories.source_repository import save_sources_metadata
from app.services import usage_service


def _docs(workspace_id, statuses):
    save_sources_metadata(
        {f"f{i}.pdf": {"status": s} for i, s in enumerate(statuses)},
        workspace_id,
    )


def test_count_documents_skips_failed():
    _docs("ws", ["Processed", "Processing", "Failed"])
    assert usage_service.count_documents("ws") == 2


def test_check_can_upload_blocks_at_limit(monkeypatch):
    monkeypatch.setitem(usage_service.PLANS["free"], "max_documents", 2)
    _docs("ws", ["Processed"])
    usage_service.check_can_upload("ws")  # below limit, no error

    _docs("ws", ["Processed", "Processed"])
    with pytest.raises(HTTPException) as exc:
        usage_service.check_can_upload("ws")
    assert exc.value.status_code == 403


def test_question_count_only_this_month_and_own_workspace():
    repo.log_conversation("ws", "q1", "a", "answered", [])
    repo.log_conversation("ws", "q2", "a", "not_found", [])
    repo.log_conversation("other", "q3", "a", "answered", [])
    repo._col().insert_one(
        {
            "_id": "old",
            "workspace_id": "ws",
            "question": "old",
            "answer": "a",
            "outcome": "answered",
            "sources": [],
            "created_at": "2000-01-01T00:00:00+00:00",
        }
    )
    assert usage_service.count_questions_this_month("ws") == 2


def test_check_can_ask_blocks_at_limit(monkeypatch):
    monkeypatch.setitem(
        usage_service.PLANS["free"], "max_questions_per_month", 2
    )
    repo.log_conversation("ws", "q1", "a", "answered", [])
    usage_service.check_can_ask("ws")  # below limit, no error

    repo.log_conversation("ws", "q2", "a", "off_topic", [])
    with pytest.raises(HTTPException) as exc:
        usage_service.check_can_ask("ws")
    assert exc.value.status_code == 429


def test_check_can_ask_fails_open(monkeypatch):
    def boom(_workspace_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(usage_service, "count_questions_this_month", boom)
    usage_service.check_can_ask("ws")  # must not raise


def test_get_usage_shape(monkeypatch):
    monkeypatch.setitem(usage_service.PLANS["free"], "max_documents", 5)
    monkeypatch.setitem(
        usage_service.PLANS["free"], "max_questions_per_month", 200
    )
    _docs("ws", ["Processed"])
    repo.log_conversation("ws", "q1", "a", "answered", [])

    assert usage_service.get_usage("ws") == {
        "plan": "free",
        "plan_name": "Free",
        "documents": 1,
        "documents_limit": 5,
        "questions": 1,
        "questions_limit": 200,
    }