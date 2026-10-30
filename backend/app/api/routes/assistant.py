from fastapi import APIRouter

from app.schemas.assistant import AssistantSettings
from app.services.assistant_service import (
    get_assistant_settings,
    update_assistant_settings,
)

router = APIRouter()


@router.get("/assistant", response_model=AssistantSettings)
def get_assistant_route():
    return get_assistant_settings()


@router.put("/assistant", response_model=AssistantSettings)
def update_assistant_route(settings: AssistantSettings):
    return update_assistant_settings(settings)