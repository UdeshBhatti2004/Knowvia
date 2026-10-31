import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from app.main import app
from app.repositories import settings_store
from app.repositories.assistant_repository import (
    load_assistant_settings,
    save_assistant_settings,
)
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


def test_get_returns_defaults_when_nothing_is_saved():
    response = client.get("/assistant")

    assert response.status_code == 200
    assert response.json() == {
        "name": DEFAULT_ASSISTANT_NAME,
        "welcome_message": DEFAULT_WELCOME_MESSAGE,
        "fallback_message": DEFAULT_FALLBACK_MESSAGE,
    }
    assert load_assistant_settings() == {}


def test_put_then_get_round_trip():
    put = client.put("/assistant", json=VALID)
    got = client.get("/assistant")

    assert put.status_code == 200
    assert put.json() == VALID
    assert got.json() == VALID
    assert load_assistant_settings() == VALID


def test_put_trims_whitespace():
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
    assert load_assistant_settings() == VALID


@pytest.mark.parametrize("field", list(VALID))
@pytest.mark.parametrize("bad_value", ["", "   "])
def test_put_rejects_blank_fields(field, bad_value):
    response = client.put("/assistant", json={**VALID, field: bad_value})

    assert response.status_code == 422
    assert load_assistant_settings() == {}


@pytest.mark.parametrize(
    "field, too_long",
    [
        ("name", "a" * 61),
        ("welcome_message", "a" * 301),
        ("fallback_message", "a" * 301),
    ],
)
def test_put_rejects_over_length_fields(field, too_long):
    response = client.put("/assistant", json={**VALID, field: too_long})

    assert response.status_code == 422
    assert load_assistant_settings() == {}


def test_put_rejects_unknown_fields():
    response = client.put("/assistant", json={**VALID, "color": "red"})

    assert response.status_code == 422
    assert load_assistant_settings() == {}


def test_put_replaces_everything_omitted_fields_reset_to_defaults():
    client.put("/assistant", json=VALID)

    response = client.put("/assistant", json={"name": "Only Name"})

    assert response.status_code == 200
    assert response.json() == {
        "name": "Only Name",
        "welcome_message": DEFAULT_WELCOME_MESSAGE,
        "fallback_message": DEFAULT_FALLBACK_MESSAGE,
    }


def test_get_falls_back_to_defaults_when_saved_values_are_invalid():
    # Saved data that breaks the rules (blank name), e.g. edited by hand.
    save_assistant_settings({**VALID, "name": ""})

    response = client.get("/assistant")

    assert response.status_code == 200
    assert response.json()["name"] == DEFAULT_ASSISTANT_NAME


def test_get_returns_500_when_the_database_fails(monkeypatch):
    def broken():
        raise PyMongoError("database down")

    monkeypatch.setattr(settings_store, "get_db", broken)

    response = client.get("/assistant")

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to read assistant settings."