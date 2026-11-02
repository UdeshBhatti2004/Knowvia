from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.auth import require_user
from app.repositories import conversation_repository

router = APIRouter()


@router.get("/conversations")
def list_conversations_route(
    outcome: Literal["answered", "not_found", "off_topic"] | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    workspace_id: str = Depends(require_user),
):
    return {
        "items": conversation_repository.list_recent(
            workspace_id, limit=limit, outcome=outcome
        )
    }


@router.get("/conversations/grouped")
def list_grouped_conversations_route(
    outcome: Literal["answered", "not_found", "off_topic"] | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    workspace_id: str = Depends(require_user),
):
    return {
        "items": conversation_repository.list_grouped(
            workspace_id, limit=limit, outcome=outcome
        )
    }