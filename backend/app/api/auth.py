from fastapi import Header, HTTPException

from app.services.auth_service import decode_token


def _bearer(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    return token if scheme.lower() == "bearer" else ""


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_account(authorization: str | None = Header(default=None)) -> dict:
    """Return the token's claims. Needs a valid token with user and workspace."""
    token = _bearer(authorization)
    claims = decode_token(token) if token else None

    if not claims or not claims.get("user_id") or not claims.get("workspace_id"):
        raise _unauthorized()

    return claims


def require_user(authorization: str | None = Header(default=None)) -> str:
    """Return the caller's workspace id."""
    return require_account(authorization)["workspace_id"]