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