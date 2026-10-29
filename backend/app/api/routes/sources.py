# APIRouter groups related URLs together (here: everything under /sources).
# BackgroundTasks lets us run a job AFTER the reply has been sent to the browser.
# File and UploadFile are how FastAPI receives an uploaded file.
from fastapi import APIRouter, BackgroundTasks, File, UploadFile

# The shape of the data that GET /sources must return.
# It also restricts "status" to the allowed values (Processing, Processed, Failed).
from app.schemas.source import SourceListResponse

# The real work lives in the service file. Routes stay thin:
# they only receive the request and pass it on.
from app.services.source_service import (
    delete_source,
    get_sources,
    upload_source,
)


router = APIRouter()


@router.post("/sources/upload")
async def upload_source_route(
    # FastAPI creates this object for each request and passes it in here.
    # We hand it to the service so the service can schedule the embedding job.
    background_tasks: BackgroundTasks,
    # The PDF the user uploaded. "..." means it is required.
    file: UploadFile = File(...),
):
    # NEW: we now also pass background_tasks. The service will reply right away
    # and run the slow embedding work later, in the background.
    return await upload_source(file, background_tasks)


# response_model makes FastAPI check the output against SourceListResponse,
# so a wrong status value would be caught instead of reaching the frontend.
@router.get("/sources", response_model=SourceListResponse)
def get_sources_route():
    return get_sources()


@router.delete("/sources/{filename}")
async def delete_source_route(filename: str):
    return await delete_source(filename)