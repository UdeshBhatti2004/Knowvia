from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import require_admin
from app.core import config
from app.services import auth_service

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login_route(payload: LoginRequest):
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