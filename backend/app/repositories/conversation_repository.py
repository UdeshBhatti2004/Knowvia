import uuid
from datetime import datetime, timezone

from app.core import db as _db

COLLECTION = "conversations"
GROUP_SCAN_LIMIT = 1000


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


def _normalize(question: str) -> str:
    text = " ".join(question.lower().split())
    return text.rstrip("?!. ")


def list_grouped(
    workspace_id: str, limit: int = 50, outcome: str | None = None
) -> list[dict]:
    """Group repeated questions (same normalized text + same outcome).

    Scans only the most recent GROUP_SCAN_LIMIT rows. Sorted by count desc,
    then most recently asked. Question/answer/sources come from the latest ask.
    """
    query = {"workspace_id": workspace_id}
    if outcome:
        query["outcome"] = outcome

    cursor = _col().find(query).sort("created_at", -1).limit(GROUP_SCAN_LIMIT)

    groups: dict[tuple[str, str], dict] = {}
    for doc in cursor:  # newest first, so first seen = latest
        key = (_normalize(doc["question"]), doc["outcome"])
        group = groups.get(key)
        if group is None:
            groups[key] = {
                "question": doc["question"],
                "answer": doc["answer"],
                "outcome": doc["outcome"],
                "sources": doc.get("sources", []),
                "count": 1,
                "last_asked": doc["created_at"],
            }
        else:
            group["count"] += 1

    items = sorted(
        groups.values(), key=lambda g: (g["count"], g["last_asked"]), reverse=True
    )
    return items[:limit]