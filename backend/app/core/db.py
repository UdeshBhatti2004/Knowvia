from pymongo import MongoClient

from app.core.config import MONGODB_DB, MONGODB_URI

_client = None


def get_db():
    """One shared client per process. Created on first use, not at import."""
    global _client

    if _client is None:
        if not MONGODB_URI:
            raise RuntimeError(
                "MONGODB_URI was not found. Check the .env file in the project root."
            )
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

    return _client[MONGODB_DB]