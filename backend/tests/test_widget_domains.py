from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import widget_repository
from app.services.domain_service import normalize_domain

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated(tmp_path):
    with patch.object(
        widget_repository, "WIDGET_SETTINGS_FILE", tmp_path / "widget.json"
    ):
        yield


def test_domains_default_empty():
    assert client.get("/widget/domains").json() == {"domains": []}


def test_put_normalizes_and_dedupes():
    response = client.put(
        "/widget/domains",
        json={"domains": ["HTTPS://Example.com/path", "example.com", " *.shop.in ", "localhost:3000"]},
    )
    assert response.status_code == 200
    assert response.json() == {
        "domains": ["example.com", "*.shop.in", "localhost:3000"]
    }
    assert client.get("/widget/domains").json() == response.json()


@pytest.mark.parametrize(
    "bad", ["", "a b.com", "evil.com; script-src *", "exa'mple.com", "http://", "-bad.com"]
)
def test_invalid_domain_rejected(bad):
    response = client.put("/widget/domains", json={"domains": [bad]})
    assert response.status_code == 422


def test_too_many_domains_rejected():
    domains = [f"site{i}.com" for i in range(21)]
    assert client.put("/widget/domains", json={"domains": domains}).status_code == 422


def test_domains_do_not_change_public_key():
    key = client.get("/widget").json()["public_key"]
    client.put("/widget/domains", json={"domains": ["example.com"]})
    assert client.get("/widget").json()["public_key"] == key


def test_normalize_domain_unit():
    assert normalize_domain("https://Foo.COM/a?b=1") == "foo.com"
