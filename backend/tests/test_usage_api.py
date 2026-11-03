from fastapi.testclient import TestClient

from app.main import app
from app.repositories import conversation_repository as repo
from app.repositories.source_repository import save_sources_metadata

client = TestClient(app)


def test_usage_returns_own_workspace_counts():
    save_sources_metadata(
        {"a.pdf": {"status": "Processed"}, "b.pdf": {"status": "Failed"}},
        "default",
    )
    repo.log_conversation("default", "q1", "a", "answered", [])
    repo.log_conversation("other", "q2", "a", "answered", [])

    res = client.get("/usage")

    assert res.status_code == 200
    body = res.json()
    assert body["documents"] == 1
    assert body["questions"] == 1
    assert body["documents_limit"] == 5
    assert body["questions_limit"] == 200


def test_usage_empty_workspace():
    res = client.get("/usage")

    assert res.status_code == 200
    assert res.json()["documents"] == 0
    assert res.json()["questions"] == 0