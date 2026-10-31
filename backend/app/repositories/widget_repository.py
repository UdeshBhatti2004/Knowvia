from app.repositories.settings_store import (
    DEFAULT_WORKSPACE_ID,
    load_settings,
    save_settings,
)

KIND = "widget"


def load_widget_settings(workspace_id=DEFAULT_WORKSPACE_ID) -> dict:
    return load_settings(KIND, workspace_id)


def save_widget_settings(settings: dict, workspace_id=DEFAULT_WORKSPACE_ID) -> None:
    save_settings(KIND, settings, workspace_id)