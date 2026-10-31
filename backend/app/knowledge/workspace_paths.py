import re
from pathlib import Path

from app.repositories.settings_store import DEFAULT_WORKSPACE_ID

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def workspace_paths(
    workspace_id: str, documents_dir: Path, cache_file: Path
) -> tuple[Path, Path]:
    """Return (documents folder, cache file) for a workspace.

    "default" keeps the existing paths. The id is checked so it can never
    point outside the data folders.
    """
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return documents_dir, cache_file

    if not _SAFE_ID.match(workspace_id or ""):
        raise ValueError("Invalid workspace id.")

    return (
        documents_dir / "workspaces" / workspace_id,
        cache_file.parent / "caches" / f"{workspace_id}.pkl",
    )