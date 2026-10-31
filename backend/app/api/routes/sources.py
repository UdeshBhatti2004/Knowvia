import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.api.auth import require_user
from app.knowledge.workspace_loader import ensure_loaded
from app.schemas.source import SourceListResponse
from app.services.source_service import (
    delete_source,
    get_sources,
    upload_source,
)


router = APIRouter()


@router.post("/sources/upload")
async def upload_source_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: str = Depends(require_user),
):
    await asyncio.to_thread(ensure_loaded, workspace_id)
    return await upload_source(file, background_tasks, workspace_id)


@router.get("/sources", response_model=SourceListResponse)
def get_sources_route(workspace_id: str = Depends(require_user)):
    ensure_loaded(workspace_id)
    return get_sources(workspace_id)


@router.delete("/sources/{filename}")
async def delete_source_route(
    filename: str, workspace_id: str = Depends(require_user)
):
    await asyncio.to_thread(ensure_loaded, workspace_id)
    return await delete_source(filename, workspace_id)