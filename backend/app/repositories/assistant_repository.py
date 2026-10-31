from app.repositories.settings_store import (
    DEFAULT_WORKSPACE_ID,
    load_settings,
    save_settings,
)

KIND = "assistant"


def load_assistant_settings(workspace_id=DEFAULT_WORKSPACE_ID) -> dict:
    return load_settings(KIND, workspace_id)


def save_assistant_settings(settings: dict, workspace_id=DEFAULT_WORKSPACE_ID) -> None:
    save_settings(KIND, settings, workspace_id)