import pytest

from app.api.auth import require_admin
from app.main import app


@pytest.fixture(autouse=True)
def bypass_admin_auth(request):
    if request.module.__name__.endswith("test_auth"):
        yield
        return

    app.dependency_overrides[require_admin] = lambda: None
    yield
    app.dependency_overrides.pop(require_admin, None)

@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    """Every test gets a fresh in-memory Mongo, never the real Atlas."""
    import mongomock

    from app.core import db

    monkeypatch.setattr(db, "_client", mongomock.MongoClient())