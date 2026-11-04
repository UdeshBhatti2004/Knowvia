import hashlib
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.auth import require_account
from app.api.client_ip import get_client_ip
from app.core import config
from app.core.passwords import hash_password, verify_password
from app.repositories import (
    password_reset_repository,
    user_repository,
    workspace_repository,
)
from app.services import auth_service, email_service
from app.services.rate_limiter import RateLimiter

router = APIRouter(prefix="/auth")

limiter = RateLimiter(config.LOGIN_RATE_LIMITS)
signup_limiter = RateLimiter(config.LOGIN_RATE_LIMITS)
password_limiter = RateLimiter(config.LOGIN_RATE_LIMITS)
forgot_limiter = RateLimiter(config.FORGOT_PASSWORD_RATE_LIMITS)
reset_limiter = RateLimiter(config.LOGIN_RATE_LIMITS)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Verified against when the email is unknown, so timing doesn't reveal accounts.
_DUMMY_HASH = hash_password("not-a-real-password")


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class SignupRequest(BaseModel):
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=200)
    workspace_name: str = Field(min_length=1, max_length=100)


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


def _throttle(rate_limiter: RateLimiter, request: Request) -> None:
    wait = rate_limiter.check(get_client_ip(request))
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(wait)},
        )


def _session(user: dict, workspace: dict) -> dict:
    return {
        "token": auth_service.create_token(
            user_id=user["_id"], workspace_id=workspace["_id"]
        ),
        "expires_in": config.AUTH_TOKEN_TTL_SECONDS,
        "email": user["email"],
        "workspace_id": workspace["_id"],
    }


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _send_reset_email(to_email: str, reset_url: str) -> None:
    # Runs after the response. A mail failure must never reach the caller,
    # or the response would reveal that the account exists.
    try:
        email_service.send_password_reset_email(to_email, reset_url)
    except Exception as exc:
        print(f"Could not send password reset email: {exc}")


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

    return _session(user, workspace)


@router.post("/login")
def login_route(payload: LoginRequest, request: Request):
    # Checked first, so guessing is throttled whatever the answer would be.
    _throttle(limiter, request)

    if not config.AUTH_SECRET:
        raise HTTPException(status_code=503, detail="Login is not configured.")

    user = user_repository.get_by_email(payload.email)
    stored = user["password_hash"] if user else _DUMMY_HASH
    ok = verify_password(payload.password, stored)

    if not user or not ok:
        raise HTTPException(status_code=401, detail="Wrong email or password.")

    workspace = workspace_repository.get_by_owner(user["_id"])
    if not workspace:
        raise HTTPException(status_code=500, detail="Workspace missing.")

    return _session(user, workspace)


@router.post("/forgot-password")
def forgot_password_route(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    _throttle(forgot_limiter, request)

    user = user_repository.get_by_email(payload.email)

    if user:
        token = secrets.token_urlsafe(32)
        password_reset_repository.create(
            user["_id"], _hash_token(token), config.PASSWORD_RESET_TTL_SECONDS
        )
        reset_url = f"{config.FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(_send_reset_email, user["email"], reset_url)

    # Same answer whether or not the account exists.
    return {"ok": True}


@router.post("/reset-password")
def reset_password_route(payload: ResetPasswordRequest, request: Request):
    _throttle(reset_limiter, request)

    invalid = HTTPException(
        status_code=400,
        detail="This reset link is invalid or has expired.",
    )

    user_id = password_reset_repository.consume(_hash_token(payload.token))
    if not user_id:
        raise invalid

    user = user_repository.get_by_id(user_id)
    if not user:
        raise invalid

    user_repository.update_password_hash(
        user_id, hash_password(payload.new_password)
    )

    return {"ok": True}


@router.get("/me")
def me_route(claims: dict = Depends(require_account)):
    user = user_repository.get_by_id(claims["user_id"])
    workspace = workspace_repository.get_by_id(claims["workspace_id"])

    if not user or not workspace:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    return {
        "ok": True,
        "email": user["email"],
        "workspace_id": workspace["_id"],
        "workspace_name": workspace["name"],
    }


@router.put("/workspace")
def update_workspace_route(
    payload: WorkspaceUpdate, claims: dict = Depends(require_account)
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name can't be empty.")

    workspace = workspace_repository.rename_workspace(claims["workspace_id"], name)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return {"ok": True, "workspace_name": workspace["name"]}


@router.put("/password")
def change_password_route(
    payload: PasswordChange,
    request: Request,
    claims: dict = Depends(require_account),
):
    _throttle(password_limiter, request)

    user = user_repository.get_by_id(claims["user_id"])
    workspace = workspace_repository.get_by_id(claims["workspace_id"])

    if not user or not workspace:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    if not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong current password.")

    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=422,
            detail="New password must be different.",
        )

    user_repository.update_password_hash(
        user["_id"], hash_password(payload.new_password)
    )

    return _session(user, workspace)