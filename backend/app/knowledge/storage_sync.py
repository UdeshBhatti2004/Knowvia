import hashlib
from pathlib import Path

from app.core.config import CACHE_FILE, DOCUMENTS_DIR
from app.knowledge.workspace_paths import workspace_paths
from app.repositories.blob_store import blob_hash, get_blob, list_blobs, put_blob
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID


def restore_from_db(workspace_id: str = DEFAULT_WORKSPACE_ID) -> None:
    """Copy a workspace's PDFs and embedding cache from Mongo to local disk.

    Called before the workspace's knowledge base is built. Errors are
    NOT caught: starting with empty folders and then pushing an empty
    cache would overwrite good data.
    """
    docs_dir, cache_file = workspace_paths(workspace_id, DOCUMENTS_DIR, CACHE_FILE)
    docs_dir.mkdir(parents=True, exist_ok=True)

    for name in list_blobs("pdf", workspace_id):
        data = get_blob("pdf", name, workspace_id)

        if data is None:
            print(f"Skipping incomplete PDF in database: {name}")
            continue

        path = docs_dir / Path(name).name

        if path.is_file() and (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == hashlib.sha256(data).hexdigest()
        ):
            continue

        path.write_bytes(data)

    cache = get_blob("cache", "embeddings", workspace_id)

    if cache is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(cache)


def push_cache(workspace_id: str = DEFAULT_WORKSPACE_ID) -> None:
    """Upload a workspace's local embedding cache to Mongo. Never raises.

    A failed push only means chunks get re-embedded after a restart.
    """
    try:
        _, cache_file = workspace_paths(workspace_id, DOCUMENTS_DIR, CACHE_FILE)

        if not cache_file.is_file():
            return

        data = cache_file.read_bytes()

        if (
            blob_hash("cache", "embeddings", workspace_id)
            == hashlib.sha256(data).hexdigest()
        ):
            return

        put_blob("cache", "embeddings", data, workspace_id)
    except Exception as exc:
        print(f"Failed to push embedding cache to database: {exc}")