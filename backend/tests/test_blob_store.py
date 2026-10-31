import hashlib

from app.core.db import get_db
from app.repositories import blob_store
from app.repositories.blob_store import (
    blob_hash,
    delete_blob,
    get_blob,
    list_blobs,
    put_blob,
)


def test_missing_blob_is_none():
    assert get_blob("pdf", "x.pdf") is None


def test_round_trip():
    put_blob("pdf", "a.pdf", b"%PDF-1")
    assert get_blob("pdf", "a.pdf") == b"%PDF-1"


def test_multi_part_round_trip(monkeypatch):
    monkeypatch.setattr(blob_store, "PART_SIZE", 4)
    data = b"0123456789abc"

    put_blob("cache", "e", data)

    assert get_db()["blob_parts"].count_documents({}) == 4
    assert get_blob("cache", "e") == data


def test_overwrite_with_shorter_data_drops_old_parts(monkeypatch):
    monkeypatch.setattr(blob_store, "PART_SIZE", 4)
    put_blob("cache", "e", b"0123456789abc")
    put_blob("cache", "e", b"abc")

    assert get_db()["blob_parts"].count_documents({}) == 1
    assert get_blob("cache", "e") == b"abc"


def test_incomplete_blob_returns_none(monkeypatch):
    monkeypatch.setattr(blob_store, "PART_SIZE", 4)
    put_blob("cache", "e", b"0123456789abc")
    get_db()["blob_parts"].delete_one({"index": 1})

    assert get_blob("cache", "e") is None


def test_delete_and_list():
    put_blob("pdf", "b.pdf", b"b")
    put_blob("pdf", "a.pdf", b"a")
    put_blob("cache", "embeddings", b"c")

    assert list_blobs("pdf") == ["a.pdf", "b.pdf"]

    delete_blob("pdf", "a.pdf")

    assert list_blobs("pdf") == ["b.pdf"]
    assert get_blob("pdf", "a.pdf") is None
    assert get_db()["blob_parts"].count_documents({"key": "default:pdf:a.pdf"}) == 0


def test_hash_matches_content():
    put_blob("cache", "embeddings", b"hello")
    assert blob_hash("cache", "embeddings") == hashlib.sha256(b"hello").hexdigest()
    assert blob_hash("cache", "missing") is None