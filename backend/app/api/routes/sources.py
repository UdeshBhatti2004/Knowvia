from fastapi import APIRouter, File, UploadFile

from app.schemas.source import SourceListResponse
from app.services.source_service import (
    delete_source,
    get_sources,
    upload_source,
)


router = APIRouter()


@router.post("/sources/upload")
async def upload_source_route(file: UploadFile = File(...)):
    return await upload_source(file)


@router.get("/sources", response_model=SourceListResponse)
def get_sources_route():
    return get_sources()


@router.delete("/sources/{filename}")
async def delete_source_route(filename: str):
    return await delete_source(filename)