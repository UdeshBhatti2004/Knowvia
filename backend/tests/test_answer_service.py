from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors

from app.services import answer_service
from app.services.answer_service import AnswerQuotaExceeded, generate_answer


class FakeAPIError(errors.APIError):
    """An API error with a chosen status code and message."""

    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code


DAILY_LIMIT_MESSAGE = (
    "429 RESOURCE_EXHAUSTED. Quota exceeded for metric: "
    "generate_content_free_tier_requests, Generate content requests per "
    "day limit exceeded on Free Tier. quotaId: "
    "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
)

PER_MINUTE_MESSAGE = (
    "429 RESOURCE_EXHAUSTED. Embed content requests per minute limit "
    "exceeded on Free Tier. quotaId: RequestsPerMinutePerProjectPerModel"
)


def fake_client(*results):
    client = MagicMock()
    client.models.generate_content.side_effect = list(results)
    return client


def test_returns_stripped_answer():
    client = fake_client(SimpleNamespace(text="  Refunds within 7 days.  "))

    with patch.object(answer_service, "client", client):
        assert generate_answer("refund?", "context") == "Refunds within 7 days."


def test_daily_quota_raises_clear_error_without_retrying():
    client = fake_client(FakeAPIError(429, DAILY_LIMIT_MESSAGE))

    with (
        patch.object(answer_service, "client", client),
        patch("app.services.answer_service.time.sleep") as sleep,
    ):
        with pytest.raises(AnswerQuotaExceeded):
            generate_answer("refund?", "context")

    assert client.models.generate_content.call_count == 1
    assert sleep.call_count == 0


def test_per_minute_limit_is_still_retried():
    client = fake_client(
        FakeAPIError(429, PER_MINUTE_MESSAGE),
        SimpleNamespace(text="Done."),
    )

    with (
        patch.object(answer_service, "client", client),
        patch("app.services.answer_service.time.sleep") as sleep,
    ):
        assert generate_answer("refund?", "context") == "Done."

    assert client.models.generate_content.call_count == 2
    assert sleep.call_count == 1


def test_server_errors_are_retried_then_raised():
    client = fake_client(
        FakeAPIError(503, "503 UNAVAILABLE."),
        FakeAPIError(503, "503 UNAVAILABLE."),
        FakeAPIError(503, "503 UNAVAILABLE."),
    )

    with (
        patch.object(answer_service, "client", client),
        patch("app.services.answer_service.time.sleep"),
    ):
        with pytest.raises(errors.APIError):
            generate_answer("refund?", "context")

    assert client.models.generate_content.call_count == 3


def test_client_errors_are_not_retried():
    client = fake_client(FakeAPIError(400, "400 INVALID_ARGUMENT."))

    with patch.object(answer_service, "client", client):
        with pytest.raises(errors.APIError):
            generate_answer("refund?", "context")

    assert client.models.generate_content.call_count == 1