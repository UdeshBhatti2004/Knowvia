from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.auth import require_claims
from app.api.client_ip import get_client_ip
from app.core import config
from app.core.passwords import hash_password, verify_password
from app.repositories import user_repository, workspace_repository
from app.services import auth_service
from app.services.rate_limiter import RateLimiter

router = APIRouter(prefix="/auth")

limiter = RateLimiter(config.LOGIN_RATE_LIMITS)
signup_limiter = RateLimiter(config.LOGIN_RATE_LIMITS)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Verified against when the email is unknown, so timing doesn't reveal accounts.
_DUMMY_HASH = hash_password("not-a-real-password")


class LoginRequest(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class SignupRequest(BaseModel):
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=200)
    workspace_name: str = Field(min_length=1, max_length=100)


def _throttle(rate_limiter: RateLimiter, request: Request) -> None:
    wait = rate_limiter.check(get_client_ip(request))
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(wait)},
        )


@router.post("/signup")
def signup_route(payload: SignupRequest, request: Request):
    _throttle(signup_limiter, request)

    if not config.AUTH_SECRET:
        raise HTTPException(status_code=503, detail="Login is not configured.")

    try:
        user = user_repository.create_user(
            payload.email, hash_password(payload.password)
        )
    except user_repository.UserExistsError:
        raise HTTPException(status_code=409, detail="Email already registered.")

    workspace = workspace_repository.create_workspace(
        user["_id"], payload.workspace_name
    )

    return {
        "token": auth_service.create_token(
            user_id=user["_id"], workspace_id=workspace["_id"]
        ),
        "expires_in": config.AUTH_TOKEN_TTL_SECONDS,
        "email": user["email"],
        "workspace_id": workspace["_id"],
    }


@router.post("/login")
def login_route(payload: LoginRequest, request: Request):
    # Checked first, so guessing is throttled whatever the answer would be.
    _throttle(limiter, request)

    if payload.email:
        return _user_login(payload.email, payload.password)

    # No email: legacy single-admin login.
    if not auth_service.is_configured():
        raise HTTPException(status_code=503, detail="Login is not configured.")

    if not auth_service.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong password.")

    return {
        "token": auth_service.create_token(),
        "expires_in": config.AUTH_TOKEN_TTL_SECONDS,
    }


def _user_login(email: str, password: str):
    if not config.AUTH_SECRET:
        raise HTTPException(status_code=503, detail="Login is not configured.")

    user = user_repository.get_by_email(email)
    stored = user["password_hash"] if user else _DUMMY_HASH
    ok = verify_password(password, stored)

    if not user or not ok:
        raise HTTPException(status_code=401, detail="Wrong email or password.")

    workspace = workspace_repository.get_by_owner(user["_id"])
    if not workspace:
        raise HTTPException(status_code=500, detail="Workspace missing.")

    return {
        "token": auth_service.create_token(
            user_id=user["_id"], workspace_id=workspace["_id"]
        ),
        "expires_in": config.AUTH_TOKEN_TTL_SECONDS,
        "email": user["email"],
        "workspace_id": workspace["_id"],
    }


@router.get("/me")
def me_route(claims: dict = Depends(require_claims)):
    user_id = claims.get("user_id")

    if not user_id:
        return {
            "ok": True,
            "email": None,
            "workspace_id": "default",
            "workspace_name": "Admin",
            "is_admin": True,
        }

    user = user_repository.get_by_id(user_id)
    workspace = workspace_repository.get_by_id(claims.get("workspace_id") or "")

    if not user or not workspace:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    return {
        "ok": True,
        "email": user["email"],
        "workspace_id": workspace["_id"],
        "workspace_name": workspace["name"],
        "is_admin": False,
    }