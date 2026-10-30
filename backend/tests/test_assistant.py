import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import assistant_repository
from app.schemas.assistant import (
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_FALLBACK_MESSAGE,
    DEFAULT_WELCOME_MESSAGE,
)

client = TestClient(app)

VALID = {
    "name": "Sunrise Bot",
    "welcome_message": "Hello!",
    "fallback_message": "Not in my documents.",
}


@pytest.fixture
def settings_file(tmp_path):
    """Point the repository at a temp file so the real one is never touched."""
    path = tmp_path / "assistant_settings.json"
    with patch.object(assistant_repository, "ASSISTANT_SETTINGS_FILE", path):
        yield path


def test_get_returns_defaults_when_nothing_is_saved(settings_file):
    response = client.get("/assistant")

    assert response.status_code == 200
    assert response.json() == {
        "name": DEFAULT_ASSISTANT_NAME,
        "welcome_message": DEFAULT_WELCOME_MESSAGE,
        "fallback_message": DEFAULT_FALLBACK_MESSAGE,
    }
    assert not settings_file.exists()


def test_put_then_get_round_trip(settings_file):
    put = client.put("/assistant", json=VALID)
    got = client.get("/assistant")

    assert put.status_code == 200
    assert put.json() == VALID
    assert got.json() == VALID
    assert json.loads(settings_file.read_text(encoding="utf-8")) == VALID
    # The temp file used for the atomic save must not be left behind.
    assert not settings_file.with_suffix(".tmp").exists()


def test_put_trims_whitespace(settings_file):
    response = client.put(
        "/assistant",
        json={
            "name": "  Sunrise Bot  ",
            "welcome_message": "  Hello!  ",
            "fallback_message": "  Not in my documents.  ",
        },
    )

    assert response.status_code == 200
    assert response.json() == VALID
    assert json.loads(settings_file.read_text(encoding="utf-8")) == VALID


@pytest.mark.parametrize("field", list(VALID))
@pytest.mark.parametrize("bad_value", ["", "   "])
def test_put_rejects_blank_fields(settings_file, field, bad_value):
    response = client.put("/assistant", json={**VALID, field: bad_value})

    assert response.status_code == 422
    assert not settings_file.exists()


@pytest.mark.parametrize(
    "field, too_long",
    [
        ("name", "a" * 61),
        ("welcome_message", "a" * 301),
        ("fallback_message", "a" * 301),
    ],
)
def test_put_rejects_over_length_fields(settings_file, field, too_long):
    response = client.put("/assistant", json={**VALID, field: too_long})

    assert response.status_code == 422
    assert not settings_file.exists()


def test_put_rejects_unknown_fields(settings_file):
    response = client.put("/assistant", json={**VALID, "color": "red"})

    assert response.status_code == 422
    assert not settings_file.exists()


def test_put_replaces_everything_omitted_fields_reset_to_defaults(settings_file):
    client.put("/assistant", json=VALID)

    response = client.put("/assistant", json={"name": "Only Name"})

    assert response.status_code == 200
    assert response.json() == {
        "name": "Only Name",
        "welcome_message": DEFAULT_WELCOME_MESSAGE,
        "fallback_message": DEFAULT_FALLBACK_MESSAGE,
    }


def test_get_falls_back_to_defaults_when_saved_values_are_invalid(settings_file):
    # Valid JSON, but a hand-edited value breaks the rules (blank name).
    settings_file.write_text(
        json.dumps({**VALID, "name": ""}), encoding="utf-8"
    )

    response = client.get("/assistant")

    assert response.status_code == 200
    assert response.json()["name"] == DEFAULT_ASSISTANT_NAME


def test_get_returns_500_when_the_file_is_not_valid_json(settings_file):
    settings_file.write_text("{ not json", encoding="utf-8")

    response = client.get("/assistant")

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to read assistant settings."