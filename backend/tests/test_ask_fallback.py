from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.routes import ask as ask_route
from app.main import app
from app.schemas.assistant import DEFAULT_FALLBACK_MESSAGE, AssistantSettings

client = TestClient(app)

CUSTOM = AssistantSettings(fallback_message="Not in my documents.")
DOC = ({"source": "fees.pdf", "page": 1, "text": "Fees are 500."}, 0.9)


def test_no_documents_uses_saved_fallback():
    with (
        patch.object(ask_route, "retrieve_knowledge", return_value=([], None)),
        patch.object(ask_route, "get_assistant_settings", return_value=CUSTOM),
    ):
        response = client.post("/ask", json={"question": "hello?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Not in my documents."


def test_model_default_sentence_is_swapped_for_saved_fallback():
    with (
        patch.object(ask_route, "retrieve_knowledge", return_value=([DOC], None)),
        patch.object(ask_route, "generate_answer", return_value=DEFAULT_FALLBACK_MESSAGE),
        patch.object(ask_route, "get_assistant_settings", return_value=CUSTOM),
    ):
        response = client.post("/ask", json={"question": "hello?"})

    assert response.json()["answer"] == "Not in my documents."


def test_normal_answer_is_left_alone():
    with (
        patch.object(ask_route, "retrieve_knowledge", return_value=([DOC], None)),
        patch.object(ask_route, "generate_answer", return_value="Fees are 500."),
        patch.object(ask_route, "get_assistant_settings", return_value=CUSTOM),
    ):
        response = client.post("/ask", json={"question": "fees?"})

    assert response.json()["answer"] == "Fees are 500."


def test_broken_settings_fall_back_to_default_instead_of_failing():
    with (
        patch.object(ask_route, "retrieve_knowledge", return_value=([], None)),
        patch.object(ask_route, "get_assistant_settings", side_effect=RuntimeError("boom")),
    ):
        response = client.post("/ask", json={"question": "hello?"})

    assert response.status_code == 200
    assert response.json()["answer"] == DEFAULT_FALLBACK_MESSAGE