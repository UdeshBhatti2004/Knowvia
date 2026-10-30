import secrets
import threading

from app.repositories.widget_repository import (
    load_widget_settings,
    save_widget_settings,
)

_lock = threading.Lock()


def get_public_key() -> str:
    """The widget's publishable key. Created on first use, then stable."""
    with _lock:
        settings = load_widget_settings()
        key = settings.get("public_key")

        if not isinstance(key, str) or not key:
            key = "wk_" + secrets.token_urlsafe(24)
            save_widget_settings({**settings, "public_key": key})

        return key


def is_valid_key(candidate: str) -> bool:
    # compare_digest avoids leaking the key through response timing.
    return secrets.compare_digest(
        candidate.encode("utf-8"),
        get_public_key().encode("utf-8"),
    )