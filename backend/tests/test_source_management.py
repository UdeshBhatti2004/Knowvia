import asyncio
from contextlib import contextmanager
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import BackgroundTasks, HTTPException, UploadFile
from fastapi.testclient import TestClient

from app.services import source_service
from main import app

client = TestClient(app)

# Tiny fake PDFs. They only need to start with "%PDF-" to pass validation.
PDF_A = b"%PDF-1.4 first document"
PDF_B = b"%PDF-1.4 second document"


def make_upload(name, content):
    """Build a fake uploaded file, like the one FastAPI gives the route."""
    return UploadFile(filename=name, file=BytesIO(content))


async def upload(name, content):
    """Run an upload and return its result AND the queued background job.

    In real life FastAPI runs the job after the reply. In a test we keep it
    in `tasks` so we can check the state before and after it runs.
    """
    tasks = BackgroundTasks()
    result = await source_service.upload_source(
        make_upload(name, content),
        tasks,
    )
    return result, tasks


@contextmanager
def fake_storage(documents_dir, metadata=None):
    """Use a temporary documents folder and in-memory metadata, and never
    touch the real knowledge base or the real files."""
    store = {} if metadata is None else metadata

    def fake_save(data):
        # Replace the in-memory "file" with the new data.
        store.clear()
        store.update(data)

    with (
        patch.object(source_service, "DOCUMENTS_DIR", documents_dir),
        # Replace the real (slow, Gemini-calling) refresh with a fake.
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


# ---------- upload ----------


def test_upload_rejects_same_content_under_a_new_name(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path) as storage:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(upload("copy.pdf", PDF_A))

    # 409 = conflict, and the message names the original file.
    assert exc_info.value.status_code == 409
    assert "first.pdf" in exc_info.value.detail
    assert not (tmp_path / "copy.pdf").exists()
    assert storage.refresh.call_count == 0


def test_upload_replies_at_once_then_processes_in_background(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path) as storage:
        result, tasks = asyncio.run(upload("second.pdf", PDF_B))

        # Right after the upload: saved, marked Processing, NOT embedded yet.
        assert result["status"] == "Processing"
        assert (tmp_path / "second.pdf").read_bytes() == PDF_B
        assert storage.refresh.call_count == 0
        assert storage.store["second.pdf"]["status"] == "Processing"

        # Now run the background job, as FastAPI would after the reply.
        asyncio.run(tasks())

    # After the job: embedded once, and the status is Processed.
    assert storage.refresh.call_count == 1
    assert storage.store["second.pdf"]["status"] == "Processed"


def test_upload_still_rejects_same_name_with_different_content(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(upload("first.pdf", PDF_B))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "A file with this name already exists."


def test_failed_processing_removes_file_and_keeps_a_failed_record(tmp_path):
    with fake_storage(tmp_path) as storage:
        # Make the embedding step crash.
        storage.refresh.side_effect = RuntimeError("Simulated embedding failure")

        _, tasks = asyncio.run(upload("second.pdf", PDF_B))
        asyncio.run(tasks())
        listed = source_service.get_sources()["sources"]

    # The file is deleted, but the "Failed" record stays so the user sees it.
    assert not (tmp_path / "second.pdf").exists()
    assert storage.store["second.pdf"]["status"] == "Failed"
    assert [item["filename"] for item in listed] == ["second.pdf"]


def test_upload_fails_cleanly_if_metadata_cannot_be_saved(tmp_path):
    with fake_storage(tmp_path) as storage:
        # Make saving the metadata crash.
        storage.save.side_effect = RuntimeError("Simulated metadata failure")
        tasks = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                source_service.upload_source(
                    make_upload("second.pdf", PDF_B),
                    tasks,
                )
            )

    # The upload is undone and no background job was scheduled.
    assert exc_info.value.status_code == 500
    assert not (tmp_path / "second.pdf").exists()
    assert len(tasks.tasks) == 0


def test_processing_is_skipped_if_the_file_was_deleted_meanwhile(tmp_path):
    with fake_storage(tmp_path) as storage:
        _, tasks = asyncio.run(upload("second.pdf", PDF_B))
        # The user deletes the document before the job gets to run.
        asyncio.run(source_service.delete_source("second.pdf"))
        refreshes_after_delete = storage.refresh.call_count

        asyncio.run(tasks())

    # The job did nothing, and the deleted document did not come back.
    assert storage.refresh.call_count == refreshes_after_delete
    assert "second.pdf" not in storage.store


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
        # Each of these must be refused with 400.
        for bad_name in ("../secret.pdf", "notes.txt", "..", ""):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(source_service.delete_source(bad_name))
            assert exc_info.value.status_code == 400

    # Nothing outside the documents folder was touched.
    assert outside.exists()
    assert (documents / "notes.txt").exists()


def test_delete_restores_file_when_refresh_fails(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path) as storage:
        storage.refresh.side_effect = RuntimeError("Simulated refresh failure")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(source_service.delete_source("first.pdf"))

    # The delete failed, so the file must be back with the same content.
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


def test_delete_clears_a_failed_record_that_has_no_file(tmp_path):
    # A failed upload: no file on disk, only a "Failed" record.
    metadata = {"bad.pdf": {"filename": "bad.pdf", "status": "Failed"}}

    with fake_storage(tmp_path, metadata) as storage:
        result = asyncio.run(source_service.delete_source("bad.pdf"))

    assert result["message"] == "Document deleted."
    assert storage.store == {}
    # No file was removed, so the knowledge base needs no refresh.
    assert storage.refresh.call_count == 0


# ---------- the HTTP routes ----------


def test_delete_route_returns_200_then_404(tmp_path):
    (tmp_path / "first.pdf").write_bytes(PDF_A)

    with fake_storage(tmp_path):
        first = client.delete("/sources/first.pdf")
        second = client.delete("/sources/first.pdf")

    assert first.status_code == 200
    assert first.json()["filename"] == "first.pdf"
    assert second.status_code == 404


def test_upload_route_returns_processing_then_finishes(tmp_path):
    with fake_storage(tmp_path) as storage:
        response = client.post(
            "/sources/upload",
            files={"file": ("second.pdf", PDF_B, "application/pdf")},
        )

    # The reply says "Processing"...
    assert response.status_code == 200
    assert response.json()["status"] == "Processing"
    # ...and the test client runs background jobs before returning, so by
    # now the job has finished too.
    assert storage.store["second.pdf"]["status"] == "Processed"



def _processing_record(name, uploaded_at):
    return {
        "filename": name,
        "size": 10,
        "uploaded_at": uploaded_at.isoformat(),
        "timestamp_is_estimated": False,
        "status": "Processing",
    }


def test_recovery_marks_processed_when_pdf_still_exists(tmp_path):
    started_at = datetime.now(timezone.utc)
    old = started_at - timedelta(hours=1)
    (tmp_path / "a.pdf").write_bytes(PDF_A)
    store = {"a.pdf": _processing_record("a.pdf", old)}

    with fake_storage(tmp_path, store):
        changed = source_service.recover_interrupted_uploads(started_at)

    assert changed == 1
    assert store["a.pdf"]["status"] == "Processed"


def test_recovery_marks_failed_when_pdf_is_missing(tmp_path):
    started_at = datetime.now(timezone.utc)
    old = started_at - timedelta(hours=1)
    store = {"gone.pdf": _processing_record("gone.pdf", old)}

    with fake_storage(tmp_path, store):
        changed = source_service.recover_interrupted_uploads(started_at)

    assert changed == 1
    assert store["gone.pdf"]["status"] == "Failed"


def test_recovery_leaves_newer_processing_records_alone(tmp_path):
    started_at = datetime.now(timezone.utc)
    newer = started_at + timedelta(minutes=1)
    (tmp_path / "live.pdf").write_bytes(PDF_B)
    store = {"live.pdf": _processing_record("live.pdf", newer)}

    with fake_storage(tmp_path, store):
        changed = source_service.recover_interrupted_uploads(started_at)

    assert changed == 0
    assert store["live.pdf"]["status"] == "Processing"


def test_recovery_ignores_records_that_are_not_processing(tmp_path):
    started_at = datetime.now(timezone.utc)
    old = started_at - timedelta(hours=1)
    done = {**_processing_record("done.pdf", old), "status": "Processed"}
    store = {"done.pdf": done}

    with fake_storage(tmp_path, store):
        changed = source_service.recover_interrupted_uploads(started_at)

    assert changed == 0
    assert store["done.pdf"]["status"] == "Processed"




def test_recovery_handles_timestamps_without_a_timezone(tmp_path):
    started_at = datetime.now(timezone.utc)
    old_naive = (started_at - timedelta(hours=1)).replace(tzinfo=None)
    new_naive = (started_at + timedelta(minutes=1)).replace(tzinfo=None)
    (tmp_path / "old.pdf").write_bytes(PDF_A)
    (tmp_path / "live.pdf").write_bytes(PDF_B)
    store = {
        "old.pdf": _processing_record("old.pdf", old_naive),
        "live.pdf": _processing_record("live.pdf", new_naive),
    }

    with fake_storage(tmp_path, store):
        changed = source_service.recover_interrupted_uploads(started_at)

    assert changed == 1
    assert store["old.pdf"]["status"] == "Processed"
    assert store["live.pdf"]["status"] == "Processing"