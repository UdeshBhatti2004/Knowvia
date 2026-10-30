from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.main import app
from app.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def configured():
    with (
        patch.object(config, "ADMIN_PASSWORD", "correct-horse"),
        patch.object(config, "AUTH_SECRET", "test-secret"),
    ):
        yield


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/sources"),
        ("get", "/assistant"),
        ("put", "/assistant"),
        ("post", "/ask"),
        ("get", "/widget"),
        ("put", "/widget/domains"),
        ("get", "/auth/me"),
    ],
)
def test_protected_routes_need_token(method, path):
    assert getattr(client, method)(path).status_code == 401


def test_domains_read_stays_open():
    assert client.get("/widget/domains").status_code == 200


def test_login_wrong_password():
    response = client.post("/auth/login", json={"password": "nope"})
    assert response.status_code == 401


def test_login_success_and_token_works():
    response = client.post("/auth/login", json={"password": "correct-horse"})
    assert response.status_code == 200
    token = response.json()["token"]
    assert client.get("/auth/me", headers=bearer(token)).status_code == 200


def test_expired_token_rejected():
    token = auth_service.create_token(ttl_seconds=-1)
    assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_tampered_token_rejected():
    token = auth_service.create_token()
    body, sig = token.split(".")
    forged = auth_service._b64(b'{"exp": 9999999999}') + "." + sig
    assert client.get("/auth/me", headers=bearer(forged)).status_code == 401
    assert client.get("/auth/me", headers=bearer(body + ".x")).status_code == 401


def test_token_from_other_secret_rejected():
    token = auth_service.create_token()
    with patch.object(config, "AUTH_SECRET", "different-secret"):
        assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_wrong_scheme_rejected():
    token = auth_service.create_token()
    response = client.get("/auth/me", headers={"Authorization": f"Basic {token}"})
    assert response.status_code == 401


def test_login_not_configured():
    with patch.object(config, "ADMIN_PASSWORD", None):
        response = client.post("/auth/login", json={"password": "x"})
    assert response.status_code == 503