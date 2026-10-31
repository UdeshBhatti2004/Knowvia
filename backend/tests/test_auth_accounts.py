import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core import config
from app.main import app
from app.services import auth_service
from app.services.rate_limiter import RateLimiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(config, "AUTH_SECRET", "test-secret")
    monkeypatch.setattr(auth_routes, "limiter", RateLimiter([(60, 1000)]))
    monkeypatch.setattr(auth_routes, "signup_limiter", RateLimiter([(60, 1000)]))


def signup(email="a@example.com", password="password123", name="Acme"):
    return client.post(
        "/auth/signup",
        json={"email": email, "password": password, "workspace_name": name},
    )


def test_signup_returns_token_with_claims():
    res = signup()
    assert res.status_code == 200
    body = res.json()
    claims = auth_service.decode_token(body["token"])
    assert claims["workspace_id"] == body["workspace_id"]
    assert claims["user_id"]
    assert body["email"] == "a@example.com"


def test_signup_token_passes_auth():
    token = signup().json()["token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_signup_duplicate_email():
    assert signup().status_code == 200
    assert signup(email="A@Example.com").status_code == 409


def test_signup_validation():
    assert signup(password="short").status_code == 422
    assert signup(email="not-an-email").status_code == 422
    assert signup(name="").status_code == 422


def test_login_with_email():
    first = signup().json()
    res = client.post(
        "/auth/login", json={"email": "A@example.com", "password": "password123"}
    )
    assert res.status_code == 200
    assert res.json()["workspace_id"] == first["workspace_id"]


def test_login_wrong_password_and_unknown_email():
    signup()
    bad_pw = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "nope-nope"}
    )
    unknown = client.post(
        "/auth/login", json={"email": "x@example.com", "password": "password123"}
    )
    assert bad_pw.status_code == 401
    assert unknown.status_code == 401
    assert bad_pw.json() == unknown.json()


def test_signup_rate_limited(monkeypatch):
    monkeypatch.setattr(auth_routes, "signup_limiter", RateLimiter([(60, 1)]))
    assert signup(email="one@example.com").status_code == 200
    assert signup(email="two@example.com").status_code == 429


def test_admin_token_has_no_account_claims(monkeypatch):
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "adminpass")
    res = client.post("/auth/login", json={"password": "adminpass"})
    assert res.status_code == 200
    claims = auth_service.decode_token(res.json()["token"])
    assert "user_id" not in claims