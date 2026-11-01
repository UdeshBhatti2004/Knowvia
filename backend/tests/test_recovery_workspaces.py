from datetime import datetime, timedelta, timezone

from app.repositories.blob_store import put_blob
from app.repositories.source_repository import (
    load_sources_metadata,
    save_sources_metadata,
)
from app.services import source_service


def record(name, uploaded_at):
    return {
        "filename": name,
        "size": 3,
        "uploaded_at": uploaded_at.isoformat(),
        "timestamp_is_estimated": False,
        "status": "Processing",
    }


OLD = datetime(2020, 1, 1, tzinfo=timezone.utc)


def test_recovers_in_every_workspace():
    started_at = datetime.now(timezone.utc)
    save_sources_metadata({"a.pdf": record("a.pdf", OLD)}, "ws1")
    save_sources_metadata({"b.pdf": record("b.pdf", OLD)}, "ws2")
    put_blob("pdf", "a.pdf", b"%PDF-aaa", "ws1")

    changed = source_service.recover_interrupted_uploads(started_at)

    assert changed == 2
    assert load_sources_metadata("ws1")["a.pdf"]["status"] == "Processed"
    assert load_sources_metadata("ws2")["b.pdf"]["status"] == "Failed"


def test_recovery_leaves_live_uploads_alone():
    started_at = datetime.now(timezone.utc)
    newer = started_at + timedelta(hours=1)
    save_sources_metadata({"c.pdf": record("c.pdf", newer)}, "ws1")

    assert source_service.recover_interrupted_uploads(started_at) == 0
    assert load_sources_metadata("ws1")["c.pdf"]["status"] == "Processing"


def test_recovery_with_nothing_to_do():
    assert source_service.recover_interrupted_uploads(datetime.now(timezone.utc)) == 0