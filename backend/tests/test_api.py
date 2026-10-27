from io import BytesIO
import asyncio
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_upload_rolls_back_file_when_metadata_save_fails(tmp_path):
    from app.services import source_service

    uploaded_file = UploadFile(
        filename="rollback_test.pdf",
        file=BytesIO(b"%PDF-1.4 test content"),
    )

    with (
        patch.object(source_service, "DOCUMENTS_DIR", tmp_path),
        patch.object(
            source_service,
            "refresh_knowledge_base",
        ) as mock_refresh,
        patch.object(
            source_service,
            "load_sources_metadata",
            return_value={},
        ),
        patch.object(
            source_service,
            "save_sources_metadata",
            side_effect=RuntimeError("Simulated metadata failure"),
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(source_service.upload_source(uploaded_file))

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == (
            "Unable to save file metadata. Please try again."
        )

        assert not (tmp_path / "rollback_test.pdf").exists()
        assert mock_refresh.call_count == 2


def test_ask_returns_fallback_when_no_document_found():
    with patch(
        "app.api.routes.ask.retrieve_knowledge",
        return_value=(None, 0.0),
    ):
        response = client.post(
            "/ask",
            json={"question": "What is the capital of France?"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "What is the capital of France?"
    assert data["answer"] == (
        "Sorry, I couldn't find relevant information "
        "in the available documents."
    )
    assert data["source"] is None


def test_ask_returns_generated_answer():
    fake_document = {
        "text": "Refund requests are allowed within 7 days.",
        "source": "business_info.pdf",
        "page": 1,
    }

    fake_results = ([(fake_document, 0.95)], 0.95)

    with (
        patch(
            "app.api.routes.ask.retrieve_knowledge",
            return_value=fake_results,
        ),
        patch(
            "app.api.routes.ask.generate_answer",
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
        patch(
            "app.api.routes.ask.retrieve_knowledge",
            return_value=fake_results,
        ),
        patch(
            "app.api.routes.ask.generate_answer",
            side_effect=RuntimeError("Simulated generation failure"),
        ),
    ):
        response = client.post(
            "/ask",
            json={"question": "What is the refund policy?"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Answer generation failed. Please try again later."
    )


def test_sources_returns_all_pdfs_and_empty_list(tmp_path):
    with (
        patch(
            "app.services.source_service.DOCUMENTS_DIR",
            tmp_path,
        ),
        patch(
            "app.services.source_service.load_sources_metadata",
            return_value={},
        ),
    ):
        assert client.get("/sources").json() == {"sources": []}

        (tmp_path / "first.pdf").write_bytes(b"%PDF-first")
        (tmp_path / "second.pdf").write_bytes(b"%PDF-second")
        (tmp_path / "ignore.txt").write_text("not a PDF")

        response = client.get("/sources")

    assert response.status_code == 200

    sources = response.json()["sources"]

    assert {source["filename"] for source in sources} == {
        "first.pdf",
        "second.pdf",
    }
    assert all(source.get("uploaded_at") for source in sources)
