from unittest.mock import patch

from fastapi.testclient import TestClient

from app.services.answer_service import AnswerQuotaExceeded
from main import app

client = TestClient(app)


def test_ask_returns_429_when_daily_answer_limit_is_reached():
    fake_document = {
        "text": "Refund requests are allowed within 7 days.",
        "source": "business_info.pdf",
        "page": 1,
    }

    with (
        patch(
            "app.api.routes.ask.retrieve_knowledge",
            return_value=([(fake_document, 0.95)], 0.95),
        ),
        patch(
            "app.api.routes.ask.generate_answer",
            side_effect=AnswerQuotaExceeded("limit"),
        ),
    ):
        response = client.post(
            "/ask",
            json={"question": "What is the refund policy?"},
        )

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "The daily answer limit has been reached. Please try again later."
    )