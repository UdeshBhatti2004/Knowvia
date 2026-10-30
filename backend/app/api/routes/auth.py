from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.auth import require_admin
from app.api.client_ip import get_client_ip
from app.core import config
from app.services import auth_service
from app.services.rate_limiter import RateLimiter

router = APIRouter(prefix="/auth")

limiter = RateLimiter(config.LOGIN_RATE_LIMITS)


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login_route(payload: LoginRequest, request: Request):
    # Checked first, so guessing is throttled whatever the answer would be.
    wait = limiter.check(get_client_ip(request))
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(wait)},
        )

    if not auth_service.is_configured():
        raise HTTPException(status_code=503, detail="Login is not configured.")

    if not auth_service.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong password.")

    return {
        "token": auth_service.create_token(),
        "expires_in": config.AUTH_TOKEN_TTL_SECONDS,
    }


@router.get("/me", dependencies=[Depends(require_admin)])
def me_route():
    return {"ok": True}