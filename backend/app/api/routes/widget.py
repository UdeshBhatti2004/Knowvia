from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
def get_widget_route():
    return {"public_key": get_public_key()}


@router.get("/widget/domains")
def get_domains_route():
    return {"domains": get_allowed_domains()}


@router.put("/widget/domains")
def put_domains_route(payload: DomainsUpdate):
    try:
        return {"domains": set_allowed_domains(payload.domains)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
