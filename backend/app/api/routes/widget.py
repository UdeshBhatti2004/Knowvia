from fastapi import APIRouter

from app.services.widget_service import get_public_key

router = APIRouter()


@router.get("/widget")
def get_widget_route():
    return {"public_key": get_public_key()}
