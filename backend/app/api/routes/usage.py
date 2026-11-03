from fastapi import APIRouter, Depends

from app.api.auth import require_user
from app.services.usage_service import get_usage

router = APIRouter()


@router.get("/usage")
def usage_route(workspace_id: str = Depends(require_user)):
    return get_usage(workspace_id)