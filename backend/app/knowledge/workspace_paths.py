import re
from pathlib import Path

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def workspace_paths(
    workspace_id: str, documents_dir: Path, cache_file: Path
) -> tuple[Path, Path]:
    """Return (documents folder, cache file) for a workspace.

    The id is checked so it can never point outside the data folders.
    """
    if not _SAFE_ID.match(workspace_id or ""):
        raise ValueError("Invalid workspace id.")

    return (
        documents_dir / "workspaces" / workspace_id,
        cache_file.parent / "caches" / f"{workspace_id}.pkl",
    )