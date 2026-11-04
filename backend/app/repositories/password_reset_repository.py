from datetime import datetime, timedelta, timezone

from app.core import db as _db

COLLECTION = "password_resets"


def _col():
    col = _db.get_db()[COLLECTION]
    # Mongo deletes expired tokens by itself. consume() still checks expiry,
    # because the TTL cleanup only runs about once a minute.
    col.create_index("expires_at", expireAfterSeconds=0)
    col.create_index("user_id")
    return col


def create(user_id: str, token_hash: str, ttl_seconds: int) -> None:
    """Store a reset token (hash only). A user has one active token."""
    col = _col()
    col.delete_many({"user_id": user_id})
    now = datetime.now(timezone.utc)
    col.insert_one(
        {
            "_id": token_hash,
            "user_id": user_id,
            "created_at": now.isoformat(),
            "expires_at": now + timedelta(seconds=ttl_seconds),
        }
    )


def consume(token_hash: str) -> str | None:
    """Use up a token. Returns the user id, or None if unknown or expired.

    The token is deleted in the same step, so it works only once.
    """
    doc = _col().find_one_and_delete({"_id": token_hash})
    if not doc:
        return None

    expires_at = doc.get("expires_at")
    if expires_at is None:
        return None
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        return None

    return doc["user_id"]