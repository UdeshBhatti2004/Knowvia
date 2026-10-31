from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import require_user
from app.services.domain_service import (
    MAX_DOMAINS,
    get_allowed_domains,
    set_allowed_domains,
)
from app.services.widget_service import get_public_key

router = APIRouter()


class DomainsUpdate(BaseModel):
    domains: list[str] = Field(max_length=MAX_DOMAINS)


@router.get("/widget")
def get_widget_route(workspace_id: str = Depends(require_user)):
    return {"public_key": get_public_key(workspace_id)}


@router.get("/widget/domains")
def get_domains_route():
    # Public (the Vercel middleware calls it). Per-workspace lookup by
    # widget key comes in the next step; for now it serves "default".
    return {"domains": get_allowed_domains()}


@router.put("/widget/domains")
def put_domains_route(
    payload: DomainsUpdate, workspace_id: str = Depends(require_user)
):
    try:
        return {"domains": set_allowed_domains(payload.domains, workspace_id)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))