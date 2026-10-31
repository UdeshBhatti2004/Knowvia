import hashlib
from pathlib import Path

from app.core.config import CACHE_FILE, DOCUMENTS_DIR
from app.repositories.blob_store import blob_hash, get_blob, list_blobs, put_blob


def restore_from_db() -> None:
    """Copy PDFs and the embedding cache from Mongo to local disk.

    Called once at startup, before the knowledge base is built. Errors are
    NOT caught: starting with empty folders and then pushing an empty
    cache would overwrite good data.
    """
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    for name in list_blobs("pdf"):
        data = get_blob("pdf", name)

        if data is None:
            print(f"Skipping incomplete PDF in database: {name}")
            continue

        path = DOCUMENTS_DIR / Path(name).name

        if path.is_file() and (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == hashlib.sha256(data).hexdigest()
        ):
            continue

        path.write_bytes(data)

    cache = get_blob("cache", "embeddings")

    if cache is not None:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_bytes(cache)


def push_cache() -> None:
    """Upload the local embedding cache to Mongo. Never raises.

    A failed push only means chunks get re-embedded after a restart.
    """
    try:
        if not CACHE_FILE.is_file():
            return

        data = CACHE_FILE.read_bytes()

        if blob_hash("cache", "embeddings") == hashlib.sha256(data).hexdigest():
            return

        put_blob("cache", "embeddings", data)
    except Exception as exc:
        print(f"Failed to push embedding cache to database: {exc}")