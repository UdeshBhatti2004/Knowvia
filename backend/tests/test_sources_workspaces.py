import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core import config
from app.knowledge import retrieval, workspace_loader
from app.main import app
from app.repositories import blob_store
from app.services import source_service
from app.services.rate_limiter import RateLimiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "AUTH_SECRET", "test-secret")
    monkeypatch.setattr(auth_routes, "limiter", RateLimiter([(60, 1000)]))
    monkeypatch.setattr(auth_routes, "signup_limiter", RateLimiter([(60, 1000)]))

    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr(source_service, "DOCUMENTS_DIR", docs)
    monkeypatch.setattr(source_service, "CACHE_FILE", tmp_path / "cache.pkl")

    from app.knowledge import storage_sync

    monkeypatch.setattr(storage_sync, "DOCUMENTS_DIR", docs)
    monkeypatch.setattr(storage_sync, "CACHE_FILE", tmp_path / "cache.pkl")

    # No real embedding calls.
    monkeypatch.setattr(source_service, "refresh_knowledge_base", lambda *a: None)
    monkeypatch.setattr(retrieval, "refresh_knowledge_base", lambda *a: None)
    monkeypatch.setattr(
        retrieval, "is_loaded", lambda workspace_id="default": True
    )


def make_user(email):
    res = client.post(
        "/auth/signup",
        json={"email": email, "password": "password123", "workspace_name": "W"},
    )
    body = res.json()
    return {"Authorization": f"Bearer {body['token']}"}, body["workspace_id"]


def upload(headers, name, content):
    return client.post(
        "/sources/upload",
        headers=headers,
        files={"file": (name, b"%PDF-1.4 " + content, "application/pdf")},
    )


def names(headers):
    res = client.get("/sources", headers=headers)
    assert res.status_code == 200
    return [s["filename"] for s in res.json()["sources"]]


def test_sources_are_isolated_between_workspaces():
    a, _ = make_user("a@example.com")
    b, _ = make_user("b@example.com")

    assert upload(a, "a.pdf", b"aaa").status_code == 200

    assert names(a) == ["a.pdf"]
    assert names(b) == []


def test_same_filename_allowed_in_different_workspaces():
    a, _ = make_user("a@example.com")
    b, _ = make_user("b@example.com")

    assert upload(a, "policy.pdf", b"one").status_code == 200
    assert upload(b, "policy.pdf", b"two").status_code == 200
    assert upload(a, "policy.pdf", b"three").status_code == 409


def test_cannot_delete_another_workspaces_file():
    a, _ = make_user("a@example.com")
    b, _ = make_user("b@example.com")
    upload(a, "a.pdf", b"aaa")

    assert client.delete("/sources/a.pdf", headers=b).status_code == 404
    assert names(a) == ["a.pdf"]
    assert client.delete("/sources/a.pdf", headers=a).status_code == 200
    assert names(a) == []


def test_blob_is_stored_under_the_workspace():
    a, ws_a = make_user("a@example.com")
    upload(a, "a.pdf", b"aaa")

    assert blob_store.get_blob("pdf", "a.pdf", ws_a) is not None
    assert blob_store.get_blob("pdf", "a.pdf") is None


def test_admin_token_uses_default_workspace(monkeypatch):
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "adminpass")
    res = client.post("/auth/login", json={"password": "adminpass"})
    admin = {"Authorization": f"Bearer {res.json()['token']}"}

    a, _ = make_user("a@example.com")
    upload(a, "a.pdf", b"aaa")

    assert names(admin) == []
    assert upload(admin, "d.pdf", b"ddd").status_code == 200
    assert names(admin) == ["d.pdf"]
    assert names(a) == ["a.pdf"]


def test_ensure_loaded_runs_restore_then_refresh_once(monkeypatch):
    calls = []
    monkeypatch.setattr(retrieval, "is_loaded", lambda w="default": bool(calls) and len(calls) >= 2)
    monkeypatch.setattr(
        workspace_loader, "restore_from_db", lambda w: calls.append(("restore", w))
    )
    monkeypatch.setattr(
        retrieval, "refresh_knowledge_base", lambda w: calls.append(("refresh", w))
    )

    workspace_loader.ensure_loaded("ws9")
    workspace_loader.ensure_loaded("ws9")

    assert calls == [("restore", "ws9"), ("refresh", "ws9")]
    workspace_loader.ensure_loaded("default")
    assert len(calls) == 2