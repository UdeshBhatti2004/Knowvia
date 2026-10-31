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


def create_token(
    ttl_seconds: int | None = None,
    user_id: str | None = None,
    workspace_id: str | None = None,
) -> str:
    ttl = config.AUTH_TOKEN_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    claims = {"exp": int(time.time()) + ttl}
    if user_id:
        claims["user_id"] = user_id
    if workspace_id:
        claims["workspace_id"] = workspace_id
    body = _b64(json.dumps(claims).encode("utf-8"))
    return f"{body}.{_sign(body)}"


def decode_token(token: str) -> dict | None:
    """Return the claims if the token is valid and unexpired, else None."""
    if not config.AUTH_SECRET:
        return None

    try:
        body, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(body)):
            return None
        payload = json.loads(_unb64(body))
        if int(payload["exp"]) <= time.time():
            return None
        return payload
    except (ValueError, KeyError, TypeError):
        return None


def verify_token(token: str) -> bool:
    return decode_token(token) is not None