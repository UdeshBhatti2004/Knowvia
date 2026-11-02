from fastapi.testclient import TestClient

from app.main import app
from app.repositories import conversation_repository as repo

client = TestClient(app)


def test_list_returns_own_workspace_only():
    repo.log_conversation("default", "mine", "a", "answered", ["fees.pdf"])
    repo.log_conversation("other", "theirs", "a", "answered", [])

    res = client.get("/conversations")

    assert res.status_code == 200
    items = res.json()["items"]
    assert [i["question"] for i in items] == ["mine"]


def test_list_filters_by_outcome():
    repo.log_conversation("default", "q1", "a", "answered", [])
    repo.log_conversation("default", "q2", "a", "not_found", [])

    res = client.get("/conversations", params={"outcome": "not_found"})

    assert [i["question"] for i in res.json()["items"]] == ["q2"]


def test_invalid_outcome_and_limit_rejected():
    assert client.get("/conversations", params={"outcome": "bad"}).status_code == 422
    assert client.get("/conversations", params={"limit": 0}).status_code == 422