import json

from fastapi import HTTPException
from pymongo.errors import PyMongoError

from app.core.db import get_db

# Single workspace for now. Multi-tenant passes a real id from the token.
DEFAULT_WORKSPACE_ID = "default"

COLLECTION = "settings"


def _doc_id(kind, workspace_id):
    return f"{workspace_id}:{kind}"


def load_settings(kind, workspace_id=DEFAULT_WORKSPACE_ID) -> dict:
    try:
        doc = get_db()[COLLECTION].find_one({"_id": _doc_id(kind, workspace_id)})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read {kind} settings.",
        ) from exc

    if not doc:
        return {}

    return json.loads(doc["data"])


def save_settings(kind, settings, workspace_id=DEFAULT_WORKSPACE_ID) -> None:
    doc_id = _doc_id(kind, workspace_id)

    try:
        get_db()[COLLECTION].replace_one(
            {"_id": doc_id},
            {
                "_id": doc_id,
                "workspace_id": workspace_id,
                "kind": kind,
                # Stored as a JSON string so keys like "fees.pdf" are safe.
                "data": json.dumps(settings),
            },
            upsert=True,
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save {kind} settings.",
        ) from exc