import threading

from pydantic import ValidationError

from app.repositories.assistant_repository import (
    load_assistant_settings,
    save_assistant_settings,
)
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID
from app.schemas.assistant import AssistantSettings

# Serializes saves so two PUTs cannot interleave.
settings_lock = threading.Lock()


def get_assistant_settings(workspace_id: str = DEFAULT_WORKSPACE_ID) -> AssistantSettings:
    """Saved settings, or defaults if nothing is saved or the data is invalid."""
    try:
        return AssistantSettings.model_validate(load_assistant_settings(workspace_id))
    except ValidationError as exc:
        print(f"Invalid assistant settings, using defaults: {exc}")
        return AssistantSettings()


def update_assistant_settings(
    settings: AssistantSettings, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> AssistantSettings:
    with settings_lock:
        save_assistant_settings(settings.model_dump(), workspace_id)
    return settings