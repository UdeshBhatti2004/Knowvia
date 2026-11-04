import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core import db
from app.core.passwords import hash_password, verify_password
from app.main import app
from app.repositories import password_reset_repository, user_repository
from app.services.rate_limiter import RateLimiter

OLD_PASSWORD = "old-password-1"
NEW_PASSWORD = "new-password-2"
EMAIL = "owner@example.com"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sent(monkeypatch):
    """Collects (email, url) instead of sending, and lifts the rate limits."""
    outbox = []
    monkeypatch.setattr(
        auth_routes.email_service,
        "send_password_reset_email",
        lambda to, url: outbox.append((to, url)),
    )
    monkeypatch.setattr(
        auth_routes, "forgot_limiter", RateLimiter([(60, 1000)])
    )
    monkeypatch.setattr(auth_routes, "reset_limiter", RateLimiter([(60, 1000)]))
    return outbox


@pytest.fixture
def user():
    return user_repository.create_user(EMAIL, hash_password(OLD_PASSWORD))


def _token(url: str) -> str:
    return url.split("token=")[1]


def test_forgot_known_email_sends_link_and_stores_only_a_hash(
    client, sent, user
):
    response = client.post("/auth/forgot-password", json={"email": EMAIL})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(sent) == 1
    to, url = sent[0]
    assert to == EMAIL
    assert "/reset-password?token=" in url

    stored = list(db.get_db()["password_resets"].find())
    assert len(stored) == 1
    assert stored[0]["_id"] != _token(url)


def test_forgot_unknown_email_looks_identical_and_sends_nothing(client, sent):
    response = client.post(
        "/auth/forgot-password", json={"email": "nobody@example.com"}
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert sent == []


def test_forgot_rejects_malformed_email(client, sent):
    response = client.post("/auth/forgot-password", json={"email": "nope"})

    assert response.status_code == 422
    assert sent == []


def test_reset_changes_password_and_token_works_once(client, sent, user):
    client.post("/auth/forgot-password", json={"email": EMAIL})
    token = _token(sent[0][1])

    first = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": NEW_PASSWORD},
    )
    assert first.status_code == 200

    stored = user_repository.get_by_email(EMAIL)["password_hash"]
    assert verify_password(NEW_PASSWORD, stored)
    assert not verify_password(OLD_PASSWORD, stored)

    second = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "another-pass-3"},
    )
    assert second.status_code == 400


def test_reset_rejects_unknown_token(client, sent, user):
    response = client.post(
        "/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400


def test_reset_rejects_expired_token(client, sent, user):
    token = "expired-token"
    password_reset_repository.create(
        user["_id"], auth_routes._hash_token(token), ttl_seconds=-60
    )

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400
    stored = user_repository.get_by_email(EMAIL)["password_hash"]
    assert verify_password(OLD_PASSWORD, stored)


def test_short_password_is_rejected_and_keeps_the_token_usable(
    client, sent, user
):
    client.post("/auth/forgot-password", json={"email": EMAIL})
    token = _token(sent[0][1])

    short = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "short"}
    )
    assert short.status_code == 422

    retry = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": NEW_PASSWORD},
    )
    assert retry.status_code == 200


def test_new_request_replaces_the_older_token(client, sent, user):
    client.post("/auth/forgot-password", json={"email": EMAIL})
    client.post("/auth/forgot-password", json={"email": EMAIL})
    old_token = _token(sent[0][1])
    new_token = _token(sent[1][1])

    old = client.post(
        "/auth/reset-password",
        json={"token": old_token, "new_password": NEW_PASSWORD},
    )
    assert old.status_code == 400

    new = client.post(
        "/auth/reset-password",
        json={"token": new_token, "new_password": NEW_PASSWORD},
    )
    assert new.status_code == 200