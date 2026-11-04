import secrets
import uuid
from datetime import datetime, timezone

from app.core import db as _db
from app.core.config import DEFAULT_PLAN

COLLECTION = "workspaces"


def _col():
    col = _db.get_db()[COLLECTION]
    col.create_index("owner_id")
    col.create_index("widget_key", unique=True)
    return col


def create_workspace(owner_id: str, name: str) -> dict:
    doc = {
        "_id": uuid.uuid4().hex,
        "owner_id": owner_id,
        "name": name.strip(),
        "widget_key": secrets.token_urlsafe(24),
        "plan": DEFAULT_PLAN,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _col().insert_one(doc)
    return doc


def get_by_id(workspace_id: str) -> dict | None:
    return _col().find_one({"_id": workspace_id})


def get_by_owner(owner_id: str) -> dict | None:
    return _col().find_one({"owner_id": owner_id})


def get_by_widget_key(widget_key: str) -> dict | None:
    return _col().find_one({"widget_key": widget_key})


def rename_workspace(workspace_id: str, name: str) -> dict | None:
    """Rename a workspace. Returns the updated doc, or None if not found."""
    result = _col().update_one(
        {"_id": workspace_id}, {"$set": {"name": name.strip()}}
    )
    if result.matched_count == 0:
        return None
    return get_by_id(workspace_id)

def mark_tested(workspace_id: str) -> None:
    """Remember that the owner ran a real test question from the dashboard."""
    _col().update_one(
        {"_id": workspace_id},
        {"$set": {"tested_at": datetime.now(timezone.utc).isoformat()}},
    )


def set_plan(workspace_id: str, plan: str) -> None:
    """Change a workspace's plan (used by billing later)."""
    _col().update_one({"_id": workspace_id}, {"$set": {"plan": plan}})