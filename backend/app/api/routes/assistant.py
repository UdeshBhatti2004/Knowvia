from fastapi import APIRouter, Depends

from app.api.auth import require_user
from app.repositories import workspace_repository
from app.schemas.assistant import AssistantSettings
from app.services.assistant_service import (
    get_assistant_settings,
    update_assistant_settings,
)

router = APIRouter()


@router.get("/assistant", response_model=AssistantSettings)
def get_assistant_route(workspace_id: str = Depends(require_user)):
    return get_assistant_settings(workspace_id)


@router.put("/assistant", response_model=AssistantSettings)
def update_assistant_route(
    settings: AssistantSettings, workspace_id: str = Depends(require_user)
):
    return update_assistant_settings(settings, workspace_id)


@router.get("/assistant/status")
def assistant_status_route(workspace_id: str = Depends(require_user)):
    workspace = workspace_repository.get_by_id(workspace_id)
    return {"tested_at": workspace.get("tested_at") if workspace else None}