import re
import threading

from app.repositories.widget_repository import (
    load_widget_settings,
    save_widget_settings,
)
from app.services.widget_service import _lock as _key_lock

MAX_DOMAINS = 20

_HOST_RE = re.compile(
    r"^(\*\.)?[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*(:\d{1,5})?$"
)


def normalize_domain(raw: str) -> str:
    value = raw.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = re.split(r"[/?#]", value, maxsplit=1)[0]

    if not value or not _HOST_RE.match(value):
        raise ValueError(f"Invalid domain: {raw!r}")

    return value


def normalize_domains(raw_domains: list[str]) -> list[str]:
    result: list[str] = []

    for raw in raw_domains:
        domain = normalize_domain(raw)
        if domain not in result:
            result.append(domain)

    if len(result) > MAX_DOMAINS:
        raise ValueError(f"At most {MAX_DOMAINS} domains are allowed.")

    return result


def get_allowed_domains() -> list[str]:
    domains = load_widget_settings().get("allowed_domains", [])
    return domains if isinstance(domains, list) else []


def set_allowed_domains(raw_domains: list[str]) -> list[str]:
    domains = normalize_domains(raw_domains)

    with _key_lock:
        settings = load_widget_settings()
        save_widget_settings({**settings, "allowed_domains": domains})

    return domains
