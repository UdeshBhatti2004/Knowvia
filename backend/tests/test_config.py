
from backend.app.core.config import (
    BACKEND_DIR,
    PROJECT_ROOT,
    DOCUMENTS_DIR,
    CACHE_FILE,
    SOURCES_METADATA_FILE,
    MAX_UPLOAD_SIZE_BYTES,
    ALLOWED_UPLOAD_EXTENSIONS,
)


def test_backend_paths():
    assert BACKEND_DIR.name == "backend"
    assert PROJECT_ROOT == BACKEND_DIR.parent
    assert DOCUMENTS_DIR == BACKEND_DIR / "documents"
    assert CACHE_FILE == BACKEND_DIR / "documents_embedding.pkl"
    assert SOURCES_METADATA_FILE == (
        DOCUMENTS_DIR / "sources_metadata.json"
    )


def test_upload_settings():
    assert MAX_UPLOAD_SIZE_BYTES == 10 * 1024 * 1024
    assert ".pdf" in ALLOWED_UPLOAD_EXTENSIONS
