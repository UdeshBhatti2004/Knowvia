from app.repositories.settings_store import load_settings, save_settings

KIND = "assistant"


def load_assistant_settings() -> dict:
    return load_settings(KIND)


def save_assistant_settings(settings: dict) -> None:
    save_settings(KIND, settings)