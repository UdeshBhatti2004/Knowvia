import pytest

from app.api.auth import require_admin, require_user
from app.main import app

# Modules that test real tokens and must not have auth bypassed.
REAL_AUTH_MODULES = (
    "test_auth",
    "test_auth_accounts",
    "test_sources_workspaces",
)


@pytest.fixture(autouse=True)
def bypass_admin_auth(request):
    if request.module.__name__.endswith(REAL_AUTH_MODULES):
        yield
        return

    app.dependency_overrides[require_admin] = lambda: None
    app.dependency_overrides[require_user] = lambda: "default"
    yield
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(require_user, None)


@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    """Every test gets a fresh in-memory Mongo, never the real Atlas."""
    import mongomock

    from app.core import db

    monkeypatch.setattr(db, "_client", mongomock.MongoClient())