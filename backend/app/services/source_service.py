import asyncio
import hashlib
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException, UploadFile

from app.core.config import (
    ALLOWED_UPLOAD_EXTENSIONS,
    CACHE_FILE,
    DOCUMENTS_DIR,
    MAX_UPLOAD_SIZE_BYTES,
)
from app.knowledge.retrieval import refresh_knowledge_base
from app.knowledge.workspace_paths import workspace_paths
from app.repositories.blob_store import delete_blob, put_blob
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID
from app.repositories.source_repository import (
    load_sources_metadata,
    save_sources_metadata,
)


# Normal requests AND background jobs all do "read, change, write back" on
# the sources metadata. This lock makes them take turns.
metadata_lock = threading.Lock()


def _docs_dir(workspace_id: str) -> Path:
    return workspace_paths(workspace_id, DOCUMENTS_DIR, CACHE_FILE)[0]


def _refresh(workspace_id: str) -> None:
    if workspace_id == DEFAULT_WORKSPACE_ID:
        refresh_knowledge_base()
    else:
        refresh_knowledge_base(workspace_id)


def _load(workspace_id: str) -> dict:
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return load_sources_metadata()
    return load_sources_metadata(workspace_id)


def _save(metadata: dict, workspace_id: str) -> None:
    if workspace_id == DEFAULT_WORKSPACE_ID:
        save_sources_metadata(metadata)
    else:
        save_sources_metadata(metadata, workspace_id)


def _put(name: str, data: bytes, workspace_id: str) -> None:
    if workspace_id == DEFAULT_WORKSPACE_ID:
        put_blob("pdf", name, data)
    else:
        put_blob("pdf", name, data, workspace_id)


def _delete(name: str, workspace_id: str) -> None:
    if workspace_id == DEFAULT_WORKSPACE_ID:
        delete_blob("pdf", name)
    else:
        delete_blob("pdf", name, workspace_id)


def _set_record(
    name: str, record: dict, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> None:
    """Add or replace the metadata record for one file."""
    with metadata_lock:
        metadata = _load(workspace_id)
        metadata[name] = record
        _save(metadata, workspace_id)


def _set_status(
    name: str, status: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> None:
    """Change only the status of an existing record.

    If the record no longer exists (deleted while processing), do nothing,
    so a deleted document is never brought back to life.
    """
    with metadata_lock:
        metadata = _load(workspace_id)
        record = metadata.get(name)

        if record is None:
            return

        metadata[name] = {**record, "status": status}
        _save(metadata, workspace_id)


def _remove_record(
    name: str,
    only_if_failed: bool = False,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> bool:
    """Delete a metadata record. Returns True if something was removed."""
    with metadata_lock:
        metadata = _load(workspace_id)
        record = metadata.get(name)

        if record is None:
            return False

        if only_if_failed and record.get("status") != "Failed":
            return False

        del metadata[name]
        _save(metadata, workspace_id)
        return True


def recover_interrupted_uploads(started_at: datetime) -> int:
    """Fix records left in "Processing" by a crash or restart (default
    workspace, called after the startup refresh succeeds).

    Only records uploaded BEFORE started_at are touched. A newer
    "Processing" record belongs to a live background job.
    """
    changed = 0

    with metadata_lock:
        metadata = load_sources_metadata()

        for name, record in metadata.items():
            if record.get("status") != "Processing":
                continue

            try:
                uploaded_at = datetime.fromisoformat(record["uploaded_at"])
            except (KeyError, TypeError, ValueError):
                uploaded_at = None
            else:
                if uploaded_at.tzinfo is None:
                    uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)

            if uploaded_at is not None and uploaded_at >= started_at:
                continue

            exists = (DOCUMENTS_DIR / name).is_file()
            metadata[name] = {
                **record,
                "status": "Processed" if exists else "Failed",
            }
            changed += 1

        if changed:
            save_sources_metadata(metadata)

    return changed


def _find_duplicate(content_hash: str, docs_dir: Path) -> str | None:
    """Return the name of a stored PDF with exactly this content, if any."""
    if not docs_dir.is_dir():
        return None

    for path in docs_dir.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        if hashlib.sha256(path.read_bytes()).hexdigest() == content_hash:
            return path.name

    return None


async def process_upload(
    filename: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> None:
    """Background job: embed the uploaded PDF, then record the outcome."""
    path = _docs_dir(workspace_id) / filename

    if not path.is_file():
        return

    try:
        await asyncio.to_thread(_refresh, workspace_id)
    except Exception as exc:
        print(f"Failed to process {filename}: {exc}")
        path.unlink(missing_ok=True)
        try:
            await asyncio.to_thread(_delete, filename, workspace_id)
        except Exception as db_exc:
            print(f"Failed to remove {filename} from database: {db_exc}")
        new_status = "Failed"
    else:
        new_status = "Processed"

    try:
        _set_status(filename, new_status, workspace_id)
    except Exception as exc:
        print(f"Failed to update status of {filename}: {exc}")


async def upload_source(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    workspace_id: str = DEFAULT_WORKSPACE_ID,
) -> dict:
    if (
        not file.filename
        or Path(file.filename).suffix.lower()
        not in ALLOWED_UPLOAD_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    content = await file.read()

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF files must be 10 MB or smaller.",
        )

    docs_dir = _docs_dir(workspace_id)
    docs_dir.mkdir(parents=True, exist_ok=True)

    duplicate_name = await asyncio.to_thread(
        _find_duplicate,
        hashlib.sha256(content).hexdigest(),
        docs_dir,
    )

    if duplicate_name:
        raise HTTPException(
            status_code=409,
            detail=(
                "This PDF has already been uploaded "
                f'as "{duplicate_name}".'
            ),
        )

    destination = docs_dir / Path(file.filename).name

    if destination.exists():
        raise HTTPException(
            status_code=409,
            detail="A file with this name already exists.",
        )

    destination.write_bytes(content)

    # The database copy is the source of truth, so store it right away.
    try:
        await asyncio.to_thread(_put, destination.name, content, workspace_id)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        print(f"Failed to store PDF in database: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to save the file. Please try again.",
        ) from exc

    record = {
        "filename": destination.name,
        "size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "timestamp_is_estimated": False,
        "status": "Processing",
    }

    try:
        _set_record(destination.name, record, workspace_id)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        try:
            await asyncio.to_thread(_delete, destination.name, workspace_id)
        except Exception as db_exc:
            print(f"Failed to remove PDF from database: {db_exc}")
        print(f"Failed to save source metadata: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to save file metadata. Please try again.",
        ) from exc

    if workspace_id == DEFAULT_WORKSPACE_ID:
        background_tasks.add_task(process_upload, destination.name)
    else:
        background_tasks.add_task(process_upload, destination.name, workspace_id)

    return {
        "message": "PDF received. Processing has started.",
        **record,
    }


async def delete_source(
    filename: str, workspace_id: str = DEFAULT_WORKSPACE_ID
) -> dict:
    safe_name = Path(filename).name

    if (
        not filename
        or safe_name != filename
        or Path(filename).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file name.",
        )

    target = _docs_dir(workspace_id) / safe_name

    if not target.is_file():
        # A failed upload has no file left, only a "Failed" record.
        if _remove_record(safe_name, True, workspace_id):
            return {
                "message": "Document deleted.",
                "filename": safe_name,
            }

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    content = target.read_bytes()

    # Remove from the database first. If this fails, nothing has changed yet.
    try:
        await asyncio.to_thread(_delete, safe_name, workspace_id)
    except Exception as exc:
        print(f"Failed to delete PDF from database: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to delete the document. Please try again.",
        ) from exc

    target.unlink()

    try:
        await asyncio.to_thread(_refresh, workspace_id)
    except Exception as exc:
        target.write_bytes(content)
        try:
            await asyncio.to_thread(_put, safe_name, content, workspace_id)
        except Exception as restore_exc:
            print(f"Failed to restore PDF in database: {restore_exc}")
        print(f"Failed to refresh knowledge base after delete: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to delete the document. Please try again.",
        ) from exc

    try:
        _remove_record(safe_name, False, workspace_id)
    except Exception as exc:
        print(f"Failed to remove source metadata: {exc}")

    return {
        "message": "Document deleted.",
        "filename": safe_name,
    }


def get_sources(workspace_id: str = DEFAULT_WORKSPACE_ID) -> dict:
    metadata = _load(workspace_id)
    docs_dir = _docs_dir(workspace_id)
    sources = []
    seen_files = set()

    paths = docs_dir.iterdir() if docs_dir.is_dir() else []

    for path in paths:
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        seen_files.add(path.name)
        record = metadata.get(path.name)

        if record:
            sources.append(record)
        else:
            # Old files from before metadata existed.
            sources.append(
                {
                    "filename": path.name,
                    "size": path.stat().st_size,
                    "uploaded_at": datetime.fromtimestamp(
                        path.stat().st_mtime,
                        tz=timezone.utc,
                    ).isoformat(),
                    "timestamp_is_estimated": True,
                    "status": "Processed",
                }
            )

    # Failed uploads have no file on disk, so add them from the metadata.
    for name, record in metadata.items():
        if name not in seen_files and record.get("status") == "Failed":
            sources.append(record)

    sources.sort(
        key=lambda source: source.get("uploaded_at", ""),
        reverse=True,
    )

    return {"sources": sources}