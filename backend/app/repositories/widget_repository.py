from app.repositories.settings_store import load_settings, save_settings

KIND = "widget"


def load_widget_settings() -> dict:
    return load_settings(KIND)


def save_widget_settings(settings: dict) -> None:
    save_settings(KIND, settings)