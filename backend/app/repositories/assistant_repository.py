import json

from fastapi import HTTPException

from app.core.config import ASSISTANT_SETTINGS_FILE


def load_assistant_settings() -> dict:
    if not ASSISTANT_SETTINGS_FILE.exists():
        return {}

    try:
        with ASSISTANT_SETTINGS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Unable to read assistant settings.",
        )


def save_assistant_settings(settings: dict) -> None:
    temporary_file = ASSISTANT_SETTINGS_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2)

        temporary_file.replace(ASSISTANT_SETTINGS_FILE)
    except OSError as exc:
        temporary_file.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to save assistant settings.",
        ) from exc