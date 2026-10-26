from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app

client = TestClient(app)

def test_ask_returns_fallback_when_no_document_found():

    with patch(
        "main.retrieve_document",
        return_value=(None, 0.0),
    ):

        response = client.post(
            "/ask",
            json={"question": "What is the capital of France?"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "What is the capital of France?"
    assert data["answer"] == "Sorry I couldn't find relevant information"
    assert data["source"] is None



def test_ask_returns_generated_answer():
    fake_document = {
        "text": "Refund requests are allowed within 7 days.",
        "source": "business_info.pdf",
        "page": 1,
    }

    fake_results = ([(fake_document, 0.95)], 0.95)

    with (
        patch("main.retrieve_document", return_value=fake_results),
        patch(
            "main.genrateAnswer",
            return_value="Refund requests are allowed within 7 days.",
        ) as mock_answer,
    ):
        response = client.post(
            "/ask",
            json={"question": "What is the refund policy?"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "Refund requests are allowed within 7 days."
    assert data["source"] == "business_info.pdf"
    assert data["page"] == 1
    assert data["similarity"] == 0.95
    assert len(data["sources"]) == 1

    mock_answer.assert_called_once()


def test_ask_returns_502_when_answer_generation_fails():
    fake_document = {
        "text": "Refund requests are allowed within 7 days.",
        "source": "business_info.pdf",
        "page": 1,
    }

    fake_results = ([(fake_document, 0.95)], 0.95)

    with (
        patch("main.retrieve_document", return_value=fake_results),
        patch(
            "main.genrateAnswer",
            side_effect=RuntimeError("Simulated generation failure"),
        ),
    ):
        response = client.post(
            "/ask",
            json={"question": "What is the refund policy?"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Answer Genration failed. Please try again later"
    )

