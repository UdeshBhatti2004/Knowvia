import base64
import hashlib
import hmac
import json
import time

from app.core import config


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body: str) -> str:
    return _b64(
        hmac.new(
            config.AUTH_SECRET.encode("utf-8"),
            body.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )


def is_configured() -> bool:
    return bool(config.ADMIN_PASSWORD and config.AUTH_SECRET)


def check_password(candidate: str) -> bool:
    if not config.ADMIN_PASSWORD:
        return False
    return hmac.compare_digest(
        candidate.encode("utf-8"), config.ADMIN_PASSWORD.encode("utf-8")
    )


def create_token(ttl_seconds: int | None = None) -> str:
    ttl = config.AUTH_TOKEN_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    payload = json.dumps({"exp": int(time.time()) + ttl}).encode("utf-8")
    body = _b64(payload)
    return f"{body}.{_sign(body)}"


def verify_token(token: str) -> bool:
    if not config.AUTH_SECRET:
        return False

    try:
        body, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(body)):
            return False
        payload = json.loads(_unb64(body))
        return int(payload["exp"]) > time.time()
    except (ValueError, KeyError, TypeError):
        return False