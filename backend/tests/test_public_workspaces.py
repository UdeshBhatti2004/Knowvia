import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.api.routes import public as public_routes
from app.core import config
from app.main import app
from app.services.rate_limiter import RateLimiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(config, "AUTH_SECRET", "test-secret")
    monkeypatch.setattr(auth_routes, "limiter", RateLimiter([(60, 1000)]))
    monkeypatch.setattr(auth_routes, "signup_limiter", RateLimiter([(60, 1000)]))
    monkeypatch.setattr(public_routes, "limiter", RateLimiter([(60, 1000)]))
    monkeypatch.setattr(public_routes, "ensure_loaded", lambda w: None)


def make_user(email):
    res = client.post(
        "/auth/signup",
        json={"email": email, "password": "password123", "workspace_name": "W"},
    )
    body = res.json()
    headers = {"Authorization": f"Bearer {body['token']}"}
    key = client.get("/widget", headers=headers).json()["public_key"]
    return headers, key


def test_invalid_key_rejected():
    assert (
        client.get("/public/assistant", headers={"X-Widget-Key": "nope"}).status_code
        == 401
    )
    assert client.get("/public/assistant").status_code == 401


def test_public_assistant_uses_workspace_settings():
    a, key_a = make_user("a@example.com")
    b, key_b = make_user("b@example.com")
    client.put(
        "/assistant",
        headers=a,
        json={
            "name": "Alpha",
            "welcome_message": "Welcome Alpha",
            "fallback_message": "none",
        },
    )

    res_a = client.get("/public/assistant", headers={"X-Widget-Key": key_a})
    res_b = client.get("/public/assistant", headers={"X-Widget-Key": key_b})

    assert res_a.json()["name"] == "Alpha"
    assert res_b.json()["name"] == "Business Assistant"


def test_public_ask_uses_workspace_fallback(monkeypatch):
    from app.api.routes import ask as ask_route

    a, key_a = make_user("a@example.com")
    client.put(
        "/assistant",
        headers=a,
        json={
            "name": "Alpha",
            "welcome_message": "Welcome",
            "fallback_message": "Alpha fallback",
        },
    )
    monkeypatch.setattr(
        ask_route, "retrieve_knowledge", lambda q, workspace_id="default": (None, 0.0)
    )

    res = client.post(
        "/public/ask",
        headers={"X-Widget-Key": key_a},
        json={"question": "anything"},
    )
    assert res.status_code == 200
    assert res.json()["answer"] == "Alpha fallback"


def test_domains_by_key():
    a, key_a = make_user("a@example.com")
    b, key_b = make_user("b@example.com")
    client.put("/widget/domains", headers=a, json={"domains": ["example.com"]})

    assert client.get("/widget/domains", params={"key": key_a}).json() == {
        "domains": ["example.com"]
    }
    assert client.get("/widget/domains", params={"key": key_b}).json() == {
        "domains": []
    }
    assert client.get("/widget/domains", params={"key": "bad"}).status_code == 404
    assert client.get("/widget/domains").json() == {"domains": []}