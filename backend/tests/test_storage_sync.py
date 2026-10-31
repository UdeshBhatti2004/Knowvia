from app.knowledge import storage_sync
from app.repositories.blob_store import get_blob, put_blob


def _paths(tmp_path, monkeypatch):
    docs = tmp_path / "documents"
    cache = tmp_path / "cache.pkl"
    monkeypatch.setattr(storage_sync, "DOCUMENTS_DIR", docs)
    monkeypatch.setattr(storage_sync, "CACHE_FILE", cache)
    return docs, cache


def test_restore_writes_pdfs_and_cache(tmp_path, monkeypatch):
    docs, cache = _paths(tmp_path, monkeypatch)
    put_blob("pdf", "fees.pdf", b"%PDF-1")
    put_blob("cache", "embeddings", b"cachebytes")

    storage_sync.restore_from_db()

    assert (docs / "fees.pdf").read_bytes() == b"%PDF-1"
    assert cache.read_bytes() == b"cachebytes"


def test_restore_with_empty_database_keeps_local_cache(tmp_path, monkeypatch):
    docs, cache = _paths(tmp_path, monkeypatch)
    cache.write_bytes(b"local")

    storage_sync.restore_from_db()

    assert cache.read_bytes() == b"local"
    assert docs.is_dir()


def test_push_cache_uploads_then_skips_unchanged(tmp_path, monkeypatch):
    _, cache = _paths(tmp_path, monkeypatch)
    cache.write_bytes(b"v1")

    storage_sync.push_cache()
    assert get_blob("cache", "embeddings") == b"v1"

    def must_not_run(*args, **kwargs):
        raise AssertionError("unchanged cache was uploaded again")

    monkeypatch.setattr(storage_sync, "put_blob", must_not_run)
    storage_sync.push_cache()  # skipped, so no AssertionError


def test_push_cache_never_raises(tmp_path, monkeypatch):
    _, cache = _paths(tmp_path, monkeypatch)
    cache.write_bytes(b"v1")

    def broken(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr(storage_sync, "put_blob", broken)
    storage_sync.push_cache()  # must not raise