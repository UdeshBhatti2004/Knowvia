import uuid
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.core import db as _db

COLLECTION = "users"


class UserExistsError(Exception):
    pass


def _col():
    col = _db.get_db()[COLLECTION]
    col.create_index("email", unique=True)
    return col


def _normalize(email: str) -> str:
    return email.strip().lower()


def create_user(email: str, password_hash: str) -> dict:
    doc = {
        "_id": uuid.uuid4().hex,
        "email": _normalize(email),
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        _col().insert_one(doc)
    except DuplicateKeyError:
        raise UserExistsError(doc["email"])
    return doc


def get_by_email(email: str) -> dict | None:
    return _col().find_one({"email": _normalize(email)})


def get_by_id(user_id: str) -> dict | None:
    return _col().find_one({"_id": user_id})