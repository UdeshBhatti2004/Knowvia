from fastapi import Header, HTTPException

from app.repositories.settings_store import DEFAULT_WORKSPACE_ID
from app.services.auth_service import decode_token, verify_token


def _bearer(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    return token if scheme.lower() == "bearer" else ""


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(authorization: str | None = Header(default=None)) -> None:
    token = _bearer(authorization)

    if not token or not verify_token(token):
        raise _unauthorized()


def require_claims(authorization: str | None = Header(default=None)) -> dict:
    """Return the token's claims, or 401."""
    token = _bearer(authorization)
    claims = decode_token(token) if token else None

    if claims is None:
        raise _unauthorized()

    return claims


def require_user(authorization: str | None = Header(default=None)) -> str:
    """Return the caller's workspace id. Admin tokens map to "default"."""
    claims = require_claims(authorization)
    return claims.get("workspace_id") or DEFAULT_WORKSPACE_ID