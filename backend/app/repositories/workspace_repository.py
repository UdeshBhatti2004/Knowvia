import secrets
import uuid
from datetime import datetime, timezone

from app.core import db as _db

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