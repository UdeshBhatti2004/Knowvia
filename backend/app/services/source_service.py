

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

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


async def upload_source(file: UploadFile) -> dict:
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

    destination = DOCUMENTS_DIR / Path(file.filename).name

    if destination.exists():
        raise HTTPException(
            status_code=409,
            detail="A file with this name already exists.",
        )

    destination.write_bytes(content)

    try:
        await asyncio.to_thread(refresh_knowledge_base)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        print(f"Failed to refresh knowledge base: {exc}")
        raise HTTPException(
            status_code=500,
            detail=(
                "PDF was not added to the knowledge base. "
                "Please try again."
            ),
        ) from exc

    record = {
        "filename": destination.name,
        "size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "timestamp_is_estimated": False,
        "status": "Processed",
    }

    try:
        metadata = load_sources_metadata()
        metadata[destination.name] = record
        save_sources_metadata(metadata)
    except Exception as exc:
        destination.unlink(missing_ok=True)

        try:
            await asyncio.to_thread(refresh_knowledge_base)
        except Exception as refresh_exc:
            print(
                "Failed to refresh knowledge base after upload rollback: "
                f"{refresh_exc}"
            )

        print(f"Failed to save source metadata: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to save file metadata. Please try again.",
        ) from exc

    return {
        "message": "PDF uploaded successfully.",
        **record,
    }


def get_sources() -> dict:
    metadata = load_sources_metadata()
    sources = []

    for path in DOCUMENTS_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        record = metadata.get(path.name)

        if record:
            sources.append(record)
        else:
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

    sources.sort(
        key=lambda source: source.get("uploaded_at", ""),
        reverse=True,
    )

    return {"sources": sources}