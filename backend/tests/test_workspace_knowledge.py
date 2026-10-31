import pytest

from app.knowledge import retrieval, storage_sync
from app.knowledge.workspace_paths import workspace_paths
from app.repositories import blob_store
from pathlib import Path


def test_default_paths_unchanged():
    docs, cache = Path("/d/documents"), Path("/d/cache.pkl")
    assert workspace_paths("default", docs, cache) == (docs, cache)


def test_workspace_paths_are_separate():
    docs, cache = Path("/d/documents"), Path("/d/cache.pkl")
    d1, c1 = workspace_paths("abc123", docs, cache)
    d2, c2 = workspace_paths("xyz789", docs, cache)
    assert d1 != d2 and c1 != c2
    assert d1 == docs / "workspaces" / "abc123"
    assert c1 == cache.parent / "caches" / "abc123.pkl"


def test_invalid_workspace_id_rejected():
    for bad in ("../x", "a/b", "", "a b"):
        with pytest.raises(ValueError):
            workspace_paths(bad, Path("/d"), Path("/c.pkl"))


def test_retrieval_is_isolated(monkeypatch):
    state = retrieval.KnowledgeBaseState(
        knowledge_base=({"source": "a.pdf", "page": 1, "text": "hello"},),
        document_embeddings=((1.0, 0.0),),
        pdf_hashes={},
        pdf_modified_time={},
    )
    monkeypatch.setitem(retrieval._states, "ws1", state)
    monkeypatch.setattr(retrieval, "get_embedding", lambda text: [1.0, 0.0])
    monkeypatch.setattr(retrieval, "decompose_query", lambda q: [q])

    docs, score = retrieval.retrieve_document("hi", "ws1")
    assert docs and docs[0][0]["source"] == "a.pdf"
    assert score > 0.99

    assert retrieval.retrieve_document("hi", "ws2") == (None, 0.0)


def test_unloaded_workspace_reports_not_loaded():
    assert not retrieval.is_loaded("never-loaded")


def test_restore_only_touches_own_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_sync, "DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr(storage_sync, "CACHE_FILE", tmp_path / "cache.pkl")

    blob_store.put_blob("pdf", "one.pdf", b"%PDF-one", "ws1")
    blob_store.put_blob("pdf", "two.pdf", b"%PDF-two", "ws2")
    blob_store.put_blob("cache", "embeddings", b"cache-ws1", "ws1")

    storage_sync.restore_from_db("ws1")

    ws1_dir = tmp_path / "documents" / "workspaces" / "ws1"
    assert [p.name for p in ws1_dir.iterdir()] == ["one.pdf"]
    assert not (tmp_path / "documents" / "workspaces" / "ws2").exists()
    assert (tmp_path / "caches" / "ws1.pkl").read_bytes() == b"cache-ws1"


def test_push_cache_stores_under_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_sync, "DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr(storage_sync, "CACHE_FILE", tmp_path / "cache.pkl")

    cache = tmp_path / "caches" / "ws1.pkl"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"data")

    storage_sync.push_cache("ws1")

    assert blob_store.get_blob("cache", "embeddings", "ws1") == b"data"
    assert blob_store.get_blob("cache", "embeddings") is None