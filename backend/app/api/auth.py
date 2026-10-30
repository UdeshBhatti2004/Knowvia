from fastapi import Header, HTTPException

from app.services.auth_service import verify_token


def require_admin(authorization: str | None = Header(default=None)) -> None:
    scheme, _, token = (authorization or "").partition(" ")

    if scheme.lower() != "bearer" or not token or not verify_token(token):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )