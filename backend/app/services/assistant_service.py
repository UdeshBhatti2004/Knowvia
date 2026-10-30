import threading

from pydantic import ValidationError

from app.repositories.assistant_repository import (
    load_assistant_settings,
    save_assistant_settings,
)
from app.schemas.assistant import AssistantSettings

# Serializes saves so two PUTs cannot interleave.
settings_lock = threading.Lock()


def get_assistant_settings() -> AssistantSettings:
    """Saved settings, or defaults if nothing is saved or the file is invalid."""
    try:
        return AssistantSettings.model_validate(load_assistant_settings())
    except ValidationError as exc:
        print(f"Invalid assistant settings on disk, using defaults: {exc}")
        return AssistantSettings()


def update_assistant_settings(settings: AssistantSettings) -> AssistantSettings:
    with settings_lock:
        save_assistant_settings(settings.model_dump())
    return settings
