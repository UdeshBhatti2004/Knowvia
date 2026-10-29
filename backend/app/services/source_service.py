import asyncio
import hashlib
import threading
from datetime import datetime, timezone
from pathlib import Path

# BackgroundTasks lets us run a job AFTER the reply has been sent.
from fastapi import BackgroundTasks, HTTPException, UploadFile

from app.core.config import (
    ALLOWED_UPLOAD_EXTENSIONS,
    DOCUMENTS_DIR,
    MAX_UPLOAD_SIZE_BYTES,
)
from app.repositories.source_repository import (
    load_sources_metadata,
    save_sources_metadata,
)
from app.knowledge.retrieval import refresh_knowledge_base


# Several things now touch sources_metadata.json: normal requests AND the
# background job. Each one does "read the file, change it, write it back".
# If two did that at the same moment, one would overwrite the other's change.
# This lock makes them take turns.
metadata_lock = threading.Lock()


def _set_record(name: str, record: dict) -> None:
    """Add or replace the metadata record for one file."""
    with metadata_lock:
        metadata = load_sources_metadata()
        metadata[name] = record
        save_sources_metadata(metadata)


def _set_status(name: str, status: str) -> None:
    """Change only the status of an existing record.

    If the record no longer exists (the user deleted the document while it
    was processing), do nothing. Otherwise we would bring a deleted
    document back to life.
    """
    with metadata_lock:
        metadata = load_sources_metadata()
        record = metadata.get(name)

        if record is None:
            return

        # Copy the old record and overwrite just the status field.
        metadata[name] = {**record, "status": status}
        save_sources_metadata(metadata)


def _remove_record(name: str, only_if_failed: bool = False) -> bool:
    """Delete a metadata record. Returns True if something was removed.

    only_if_failed=True is used when a file is already gone from disk: we
    only clear the record if it is a "Failed" one, so we never hide a
    record that should still be there.
    """
    with metadata_lock:
        metadata = load_sources_metadata()
        record = metadata.get(name)

        if record is None:
            return False

        if only_if_failed and record.get("status") != "Failed":
            return False

        del metadata[name]
        save_sources_metadata(metadata)
        return True


def _find_duplicate(content_hash: str) -> str | None:
    """Return the name of a stored PDF with exactly this content, if any."""
    if not DOCUMENTS_DIR.is_dir():
        return None

    for path in DOCUMENTS_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        # Same hash = same content, whatever the file is called.
        if hashlib.sha256(path.read_bytes()).hexdigest() == content_hash:
            return path.name

    return None


async def process_upload(filename: str) -> None:
    """Background job: embed the uploaded PDF, then record the outcome.

    This runs AFTER the browser already got its reply, so it can take as
    long as it needs (including the rate-limit pauses).
    """
    path = DOCUMENTS_DIR / filename

    # The user deleted the file before this job even started: nothing to do.
    if not path.is_file():
        return

    try:
        # refresh_knowledge_base is slow and blocking, so we run it in a
        # separate thread. This keeps the server responsive to other users.
        await asyncio.to_thread(refresh_knowledge_base)
    except Exception as exc:
        print(f"Failed to process {filename}: {exc}")
        # Remove the file so the folder and the knowledge base agree.
        path.unlink(missing_ok=True)
        new_status = "Failed"
    else:
        new_status = "Processed"

    try:
        _set_status(filename, new_status)
    except Exception as exc:
        # Nobody is waiting for this job, so we can only log the problem.
        print(f"Failed to update status of {filename}: {exc}")


async def upload_source(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> dict:
    # --- Validation (same checks as before) ---

    # Only .pdf file names are accepted.
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

    # A real PDF starts with "%PDF-". This catches renamed non-PDF files.
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

    # Refuse the same content under a different name.
    duplicate_name = await asyncio.to_thread(
        _find_duplicate,
        hashlib.sha256(content).hexdigest(),
    )

    if duplicate_name:
        raise HTTPException(
            status_code=409,
            detail=(
                "This PDF has already been uploaded "
                f'as "{duplicate_name}".'
            ),
        )

    # Path(...).name strips any folder parts, so a name like
    # "../../x.pdf" cannot escape the documents folder.
    destination = DOCUMENTS_DIR / Path(file.filename).name

    if destination.exists():
        raise HTTPException(
            status_code=409,
            detail="A file with this name already exists.",
        )

    # --- Save quickly, process later ---

    destination.write_bytes(content)

    # NEW: the record starts as "Processing", not "Processed".
    record = {
        "filename": destination.name,
        "size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "timestamp_is_estimated": False,
        "status": "Processing",
    }

    try:
        _set_record(destination.name, record)
    except Exception as exc:
        # If we cannot even record the file, undo the save and report it.
        destination.unlink(missing_ok=True)
        print(f"Failed to save source metadata: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to save file metadata. Please try again.",
        ) from exc

    # NEW: schedule the slow embedding job. FastAPI runs it only after the
    # reply below has been sent, so the browser does not wait for it.
    background_tasks.add_task(process_upload, destination.name)

    return {
        "message": "PDF received. Processing has started.",
        **record,
    }


async def delete_source(filename: str) -> dict:
    # Only a plain "name.pdf" is accepted: no folders, no "..", no other types.
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

    target = DOCUMENTS_DIR / safe_name

    if not target.is_file():
        # NEW: a failed upload has no file left, only a "Failed" record.
        # Deleting it just clears that record from the list.
        if _remove_record(safe_name, only_if_failed=True):
            return {
                "message": "Document deleted.",
                "filename": safe_name,
            }

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # Keep a copy of the content so we can restore the file if refreshing
    # the knowledge base fails.
    content = target.read_bytes()
    target.unlink()

    try:
        await asyncio.to_thread(refresh_knowledge_base)
    except Exception as exc:
        # Put the file back so the knowledge base and the folder agree.
        target.write_bytes(content)
        print(f"Failed to refresh knowledge base after delete: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to delete the document. Please try again.",
        ) from exc

    # The file is gone and search is updated. A leftover metadata entry is
    # harmless (the list only shows files that exist), so don't fail on it.
    try:
        _remove_record(safe_name)
    except Exception as exc:
        print(f"Failed to remove source metadata: {exc}")

    return {
        "message": "Document deleted.",
        "filename": safe_name,
    }


def get_sources() -> dict:
    metadata = load_sources_metadata()
    sources = []
    # Remember which files exist on disk, to find "Failed" records later.
    seen_files = set()

    for path in DOCUMENTS_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        seen_files.add(path.name)
        record = metadata.get(path.name)

        if record:
            sources.append(record)
        else:
            # Old files from before metadata existed: build a record from
            # the file itself and mark the date as estimated.
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

    # NEW: failed uploads have no file on disk, so the loop above cannot
    # see them. Add them from the metadata so the user can see the failure.
    for name, record in metadata.items():
        if name not in seen_files and record.get("status") == "Failed":
            sources.append(record)

    # Newest first.
    sources.sort(
        key=lambda source: source.get("uploaded_at", ""),
        reverse=True,
    )

    return {"sources": sources}