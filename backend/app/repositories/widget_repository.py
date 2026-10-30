import json

from fastapi import HTTPException

from app.core.config import WIDGET_SETTINGS_FILE


def load_widget_settings() -> dict:
    if not WIDGET_SETTINGS_FILE.exists():
        return {}

    try:
        with WIDGET_SETTINGS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Unable to read widget settings.",
        )


def save_widget_settings(settings: dict) -> None:
    temporary_file = WIDGET_SETTINGS_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2)

        temporary_file.replace(WIDGET_SETTINGS_FILE)
    except OSError as exc:
        temporary_file.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to save widget settings.",
        ) from exc