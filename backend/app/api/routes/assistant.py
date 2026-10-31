from fastapi import APIRouter, Depends

from app.api.auth import require_user
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