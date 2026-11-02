import uuid
from datetime import datetime, timezone

from app.core import db as _db

COLLECTION = "conversations"


def _col():
    col = _db.get_db()[COLLECTION]
    col.create_index([("workspace_id", 1), ("created_at", -1)])
    return col


def log_conversation(
    workspace_id: str,
    question: str,
    answer: str,
    outcome: str,
    sources: list[str],
) -> None:
    """outcome is 'answered', 'not_found' or 'off_topic'."""
    _col().insert_one(
        {
            "_id": uuid.uuid4().hex,
            "workspace_id": workspace_id,
            "question": question,
            "answer": answer,
            "outcome": outcome,
            "sources": sources,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def list_recent(
    workspace_id: str, limit: int = 50, outcome: str | None = None
) -> list[dict]:
    query = {"workspace_id": workspace_id}
    if outcome:
        query["outcome"] = outcome

    cursor = _col().find(query).sort("created_at", -1).limit(limit)
    return [
        {
            "id": doc["_id"],
            "question": doc["question"],
            "answer": doc["answer"],
            "outcome": doc["outcome"],
            "sources": doc.get("sources", []),
            "created_at": doc["created_at"],
        }
        for doc in cursor
    ]