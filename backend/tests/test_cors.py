from fastapi.testclient import TestClient

from app.core.config import parse_origins
from app.main import app

client = TestClient(app)


def test_parse_origins_trims_and_drops_empty():
    raw = " https://a.com/ , ,https://b.com "
    assert parse_origins(raw) == ["https://a.com", "https://b.com"]


def test_cors_allows_listed_origin():
    r = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_blocks_unlisted_origin():
    r = client.get("/", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers