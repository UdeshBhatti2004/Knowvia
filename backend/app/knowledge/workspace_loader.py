import threading

from app.knowledge import retrieval
from app.knowledge.storage_sync import restore_from_db

_registry_lock = threading.Lock()
_load_locks: dict[str, threading.Lock] = {}


def ensure_loaded(workspace_id: str) -> None:
    """Build a workspace's knowledge base the first time it is needed.

    Errors are not caught, so a failed load is retried on the next request
    instead of serving an empty workspace.
    """
    if retrieval.is_loaded(workspace_id):
        return

    with _registry_lock:
        lock = _load_locks.setdefault(workspace_id, threading.Lock())

    with lock:
        if retrieval.is_loaded(workspace_id):
            return

        restore_from_db(workspace_id)
        retrieval.refresh_knowledge_base(workspace_id)