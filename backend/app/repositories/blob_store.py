import hashlib

from app.core.db import get_db
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID

# Parts stay far below Mongo's 16 MB document limit.
PART_SIZE = 4 * 1024 * 1024

META = "blobs"
PARTS = "blob_parts"


def _key(kind, name, workspace_id):
    return f"{workspace_id}:{kind}:{name}"


def put_blob(kind, name, data, workspace_id=DEFAULT_WORKSPACE_ID) -> None:
    """Store bytes under (kind, name), replacing any old version.

    Raises PyMongoError on failure. The metadata doc is written last, so a
    crash mid-write leaves a blob that get_blob treats as missing.
    """
    db = get_db()
    key = _key(kind, name, workspace_id)
    chunks = [
        data[i:i + PART_SIZE] for i in range(0, len(data), PART_SIZE)
    ] or [b""]

    db[PARTS].delete_many({"key": key})
    db[PARTS].insert_many(
        [
            {"_id": f"{key}#{i}", "key": key, "index": i, "data": chunk}
            for i, chunk in enumerate(chunks)
        ]
    )
    db[META].replace_one(
        {"_id": key},
        {
            "_id": key,
            "workspace_id": workspace_id,
            "kind": kind,
            "name": name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "count": len(chunks),
        },
        upsert=True,
    )


def get_blob(kind, name, workspace_id=DEFAULT_WORKSPACE_ID):
    """Return the stored bytes, or None if missing or incomplete."""
    db = get_db()
    key = _key(kind, name, workspace_id)

    meta = db[META].find_one({"_id": key})
    if not meta:
        return None

    parts = list(db[PARTS].find({"key": key}).sort("index", 1))
    if len(parts) != meta["count"]:
        return None

    data = b"".join(part["data"] for part in parts)
    if hashlib.sha256(data).hexdigest() != meta["sha256"]:
        return None

    return data


def blob_hash(kind, name, workspace_id=DEFAULT_WORKSPACE_ID):
    meta = get_db()[META].find_one({"_id": _key(kind, name, workspace_id)})
    return meta["sha256"] if meta else None


def delete_blob(kind, name, workspace_id=DEFAULT_WORKSPACE_ID) -> None:
    db = get_db()
    key = _key(kind, name, workspace_id)
    db[META].delete_one({"_id": key})
    db[PARTS].delete_many({"key": key})


def list_blobs(kind, workspace_id=DEFAULT_WORKSPACE_ID) -> list:
    docs = get_db()[META].find({"workspace_id": workspace_id, "kind": kind})
    return sorted(doc["name"] for doc in docs)