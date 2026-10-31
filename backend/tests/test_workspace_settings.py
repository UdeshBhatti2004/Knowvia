import pytest
from fastapi.testclient import TestClient

from app.api.routes import ask as ask_route
from app.api.routes import auth as auth_routes
from app.core import config
from app.main import app
from app.repositories import workspace_repository
from app.services.rate_limiter import RateLimiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(config, "AUTH_SECRET", "test-secret")
    monkeypatch.setattr(auth_routes, "limiter", RateLimiter([(60, 1000)]))
    monkeypatch.setattr(auth_routes, "signup_limiter", RateLimiter([(60, 1000)]))


def make_user(email):
    res = client.post(
        "/auth/signup",
        json={"email": email, "password": "password123", "workspace_name": "W"},
    )
    body = res.json()
    return {"Authorization": f"Bearer {body['token']}"}, body["workspace_id"]


def settings(name):
    return {
        "name": name,
        "welcome_message": f"Welcome to {name}",
        "fallback_message": f"{name} has no answer",
    }


def test_assistant_settings_are_isolated():
    a, _ = make_user("a@example.com")
    b, _ = make_user("b@example.com")

    assert client.put("/assistant", headers=a, json=settings("Alpha")).status_code == 200

    assert client.get("/assistant", headers=a).json()["name"] == "Alpha"
    assert client.get("/assistant", headers=b).json()["name"] == "Business Assistant"


def test_widget_key_is_the_workspaces_own():
    a, ws_a = make_user("a@example.com")
    b, ws_b = make_user("b@example.com")

    key_a = client.get("/widget", headers=a).json()["public_key"]
    key_b = client.get("/widget", headers=b).json()["public_key"]

    assert key_a == workspace_repository.get_by_id(ws_a)["widget_key"]
    assert key_b == workspace_repository.get_by_id(ws_b)["widget_key"]
    assert key_a != key_b


def test_allowed_domains_are_isolated():
    a, _ = make_user("a@example.com")
    b, _ = make_user("b@example.com")

    res = client.put("/widget/domains", headers=a, json={"domains": ["example.com"]})
    assert res.json() == {"domains": ["example.com"]}

    assert client.get("/widget/domains").json() == {"domains": []}
    assert client.put("/widget/domains", headers=b, json={"domains": []}).json() == {
        "domains": []
    }


def test_ask_uses_the_workspaces_fallback(monkeypatch):
    a, _ = make_user("a@example.com")
    b, _ = make_user("b@example.com")
    client.put("/assistant", headers=a, json=settings("Alpha"))

    monkeypatch.setattr(ask_route, "ensure_loaded", lambda w: None)
    monkeypatch.setattr(
        ask_route, "retrieve_knowledge", lambda q, workspace_id="default": (None, 0.0)
    )

    ans_a = client.post("/ask", headers=a, json={"question": "hi"}).json()["answer"]
    ans_b = client.post("/ask", headers=b, json={"question": "hi"}).json()["answer"]

    assert ans_a == "Alpha has no answer"
    assert ans_b != ans_a


def test_admin_token_still_uses_default_workspace(monkeypatch):
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "adminpass")
    res = client.post("/auth/login", json={"password": "adminpass"})
    admin = {"Authorization": f"Bearer {res.json()['token']}"}

    a, _ = make_user("a@example.com")
    client.put("/assistant", headers=a, json=settings("Alpha"))

    assert client.get("/assistant", headers=admin).json()["name"] == "Business Assistant"
    assert client.get("/widget", headers=admin).json()["public_key"].startswith("wk_")