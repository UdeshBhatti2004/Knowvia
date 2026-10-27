
from fastapi import APIRouter, File, UploadFile

from app.services.source_service import (
    get_sources,
    upload_source,
)


router = APIRouter()


@router.post("/sources/upload")
async def upload_source_route(file: UploadFile = File(...)):
    return await upload_source(file)


@router.get("/sources")
def get_sources_route():
    return get_sources()
