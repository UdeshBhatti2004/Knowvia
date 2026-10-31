import secrets
import threading

from app.repositories import workspace_repository
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID
from app.repositories.widget_repository import (
    load_widget_settings,
    save_widget_settings,
)

_lock = threading.Lock()


def get_public_key(workspace_id: str = DEFAULT_WORKSPACE_ID) -> str:
    """The workspace's publishable key.

    Real workspaces get theirs at signup. "default" (the admin workspace)
    creates one on first use, then it stays stable.
    """
    if workspace_id != DEFAULT_WORKSPACE_ID:
        workspace = workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise LookupError("Workspace not found.")
        return workspace["widget_key"]

    with _lock:
        settings = load_widget_settings()
        key = settings.get("public_key")

        if not isinstance(key, str) or not key:
            key = "wk_" + secrets.token_urlsafe(24)
            save_widget_settings({**settings, "public_key": key})

        return key


def is_valid_key(candidate: str) -> bool:
    # compare_digest avoids leaking the key through response timing.
    return secrets.compare_digest(
        candidate.encode("utf-8"),
        get_public_key().encode("utf-8"),
    )


def resolve_workspace(candidate: str) -> str | None:
    """Return the workspace id for a widget key, or None if it's unknown."""
    if not candidate:
        return None

    # Legacy key of the "default" workspace.
    if is_valid_key(candidate):
        return DEFAULT_WORKSPACE_ID

    workspace = workspace_repository.get_by_widget_key(candidate)
    return workspace["_id"] if workspace else None