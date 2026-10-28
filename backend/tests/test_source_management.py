import asyncio
from contextlib import contextmanager
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from app.services import source_service
from main import app

client = TestClient(app)

PDF_A = b"%PDF-1.4 first document"
PDF_B = b"%PDF-1.4 second document"


def make_upload(name, content):
    return UploadFile(filename=name, file=BytesIO(content))


@contextmanager
def fake_storage(documents_dir, metadata=None):
    """Use a temporary documents folder and in-memory metadata, and never
    touch the real knowledge base."""
    store = {} if metadata is None else metadata

    def fake_save(data):
        store.clear()
        store.update(data)

    with (
        patch.object(source_service, "DOCUMENTS_DIR", documents_dir),
        patch.object(source_service, "refresh_knowledge_base") as refresh,
        patch.object(
            source_service,
            "load_sources_metadata",
            side_effect=lambda: dict(store),
        ),
        patch.object(
            source_service,
            "save_sources_metadata",
            side_effect=fake_save,
        ) as save,
    ):
        yield SimpleNamespace(refresh=refresh, save=save, store=store)


# ---------- duplicate uploads ----------


def test_upload_rejects_same_content_under_a_new_name(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path) as storage:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                source_service.upload_source(make_upload("copy.pdf", PDF_A))
            )

    assert exc_info.value.status_code == 409
    assert "first.pdf" in exc_info.value.detail
    assert not (tmp_path / "copy.pdf").exists()
    assert storage.refresh.call_count == 0


def test_upload_accepts_new_content(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path) as storage:
        result = asyncio.run(
            source_service.upload_source(make_upload("second.pdf", PDF_B))
        )

    assert result["message"] == "PDF uploaded successfully."
    assert (tmp_path / "second.pdf").read_bytes() == PDF_B
    assert storage.refresh.call_count == 1
    assert "second.pdf" in storage.store


def test_upload_still_rejects_same_name_with_different_content(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                source_service.upload_source(make_upload("first.pdf", PDF_B))
            )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "A file with this name already exists."


# ---------- delete ----------


def test_delete_removes_file_metadata_and_refreshes(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)
    (tmp_path / "second.pdf").write_bytes(PDF_B)
    metadata = {
        "first.pdf": {"filename": "first.pdf"},
        "second.pdf": {"filename": "second.pdf"},
    }

    with fake_storage(tmp_path, metadata) as storage:
        result = asyncio.run(source_service.delete_source("first.pdf"))

    assert result == {"message": "Document deleted.", "filename": "first.pdf"}
    assert not (tmp_path / "first.pdf").exists()
    assert (tmp_path / "second.pdf").exists()
    assert storage.refresh.call_count == 1
    assert set(storage.store) == {"second.pdf"}


def test_delete_unknown_file_returns_404(tmp_path):
    with fake_storage(tmp_path) as storage:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(source_service.delete_source("missing.pdf"))

    assert exc_info.value.status_code == 404
    assert storage.refresh.call_count == 0


def test_delete_rejects_paths_and_non_pdf_names(tmp_path):
    documents = tmp_path / "docs"
    documents.mkdir()
    outside = tmp_path / "secret.pdf"
    outside.write_bytes(PDF_A)
    (documents / "notes.txt").write_text("keep me")

    with fake_storage(documents):
        for bad_name in ("../secret.pdf", "notes.txt", "..", ""):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(source_service.delete_source(bad_name))
            assert exc_info.value.status_code == 400

    assert outside.exists()
    assert (documents / "notes.txt").exists()


def test_delete_restores_file_when_refresh_fails(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path) as storage:
        storage.refresh.side_effect = RuntimeError("Simulated refresh failure")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(source_service.delete_source("first.pdf"))

    assert exc_info.value.status_code == 500
    assert (tmp_path / "first.pdf").read_bytes() == PDF_A


def test_delete_succeeds_even_if_metadata_cannot_be_saved(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)
    metadata = {"first.pdf": {"filename": "first.pdf"}}

    with fake_storage(tmp_path, metadata) as storage:
        storage.save.side_effect = RuntimeError("Simulated metadata failure")
        result = asyncio.run(source_service.delete_source("first.pdf"))

    assert result["message"] == "Document deleted."
    assert not (tmp_path / "first.pdf").exists()


# ---------- the HTTP route ----------


def test_delete_route_returns_200_then_404(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path):
        first = client.delete("/sources/first.pdf")
        second = client.delete("/sources/first.pdf")

    assert first.status_code == 200
    assert first.json()["filename"] == "first.pdf"
    assert second.status_code == 404