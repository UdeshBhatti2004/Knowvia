
import json

from fastapi import HTTPException

from app.core.config import SOURCES_METADATA_FILE


def load_sources_metadata() -> dict:
    if not SOURCES_METADATA_FILE.exists():
        return {}

    try:
        with SOURCES_METADATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Unable to read uploaded-file metadata.",
        )


def save_sources_metadata(metadata: dict) -> None:
    temporary_file = SOURCES_METADATA_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        temporary_file.replace(SOURCES_METADATA_FILE)
    except OSError as exc:
        temporary_file.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to save file metadata.",
        ) from exc
