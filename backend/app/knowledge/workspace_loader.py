import threading

from app.knowledge import retrieval
from app.knowledge.storage_sync import restore_from_db
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID

_registry_lock = threading.Lock()
_load_locks: dict[str, threading.Lock] = {}


def ensure_loaded(workspace_id: str) -> None:
    """Build a workspace's knowledge base the first time it is needed.

    "default" is built at startup. Errors are not caught, so a failed load
    is retried on the next request instead of serving an empty workspace.
    """
    if workspace_id == DEFAULT_WORKSPACE_ID or retrieval.is_loaded(workspace_id):
        return

    with _registry_lock:
        lock = _load_locks.setdefault(workspace_id, threading.Lock())

    with lock:
        if retrieval.is_loaded(workspace_id):
            return

        restore_from_db(workspace_id)
        retrieval.refresh_knowledge_base(workspace_id)