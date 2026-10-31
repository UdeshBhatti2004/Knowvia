from fastapi import HTTPException
from pymongo.errors import PyMongoError

from app.core.db import get_db
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID

COLLECTION = "sources"


def load_sources_metadata(workspace_id=DEFAULT_WORKSPACE_ID) -> dict:
    try:
        docs = get_db()[COLLECTION].find({"workspace_id": workspace_id})
        return {doc["name"]: doc["record"] for doc in docs}
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to read uploaded-file metadata.",
        ) from exc


def save_sources_metadata(metadata: dict, workspace_id=DEFAULT_WORKSPACE_ID) -> None:
    try:
        collection = get_db()[COLLECTION]

        for name, record in metadata.items():
            doc_id = f"{workspace_id}:{name}"
            collection.replace_one(
                {"_id": doc_id},
                {
                    "_id": doc_id,
                    "workspace_id": workspace_id,
                    "name": name,
                    "record": record,
                },
                upsert=True,
            )

        # Records dropped from the dict are deleted, like the old file rewrite.
        collection.delete_many(
            {"workspace_id": workspace_id, "name": {"$nin": list(metadata)}}
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to save file metadata.",
        ) from exc