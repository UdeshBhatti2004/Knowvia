import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.api.client_ip import get_client_ip
from app.api.routes.ask import ask_question
from app.core.config import PUBLIC_RATE_LIMITS
from app.knowledge.workspace_loader import ensure_loaded
from app.schemas.question import QuestionRequest
from app.services.assistant_service import get_assistant_settings
from app.services.rate_limiter import RateLimiter
from app.services.widget_service import resolve_workspace

limiter = RateLimiter(PUBLIC_RATE_LIMITS)


def require_widget_key(x_widget_key: str | None = Header(default=None)) -> str:
    """Return the workspace id that owns the widget key."""
    workspace_id = resolve_workspace(x_widget_key or "")

    if workspace_id is None:
        raise HTTPException(status_code=401, detail="Invalid widget key.")

    return workspace_id


def enforce_rate_limit(request: Request) -> None:
    ip = get_client_ip(request)
    wait = limiter.check(ip)

    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many questions. Please wait a moment and try again.",
            headers={"Retry-After": str(wait)},
        )


router = APIRouter(prefix="/public")


class PublicQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty or whitespace.")
        return value


class PublicSource(BaseModel):
    source: str
    page: int | str | None = None


class PublicAnswer(BaseModel):
    answer: str
    sources: list[PublicSource]


class PublicAssistant(BaseModel):
    name: str
    welcome_message: str


@router.get("/assistant", response_model=PublicAssistant)
def public_assistant_route(workspace_id: str = Depends(require_widget_key)):
    settings = get_assistant_settings(workspace_id)
    return {
        "name": settings.name,
        "welcome_message": settings.welcome_message,
    }


@router.post(
    "/ask",
    response_model=PublicAnswer,
    dependencies=[Depends(enforce_rate_limit)],
)
async def public_ask_route(
    body: PublicQuestion, workspace_id: str = Depends(require_widget_key)
):
    await asyncio.to_thread(ensure_loaded, workspace_id)

    # Same retrieval and answer logic as the dashboard /ask.
    result = await asyncio.to_thread(
        ask_question, QuestionRequest(question=body.question), workspace_id
    )

    # Only what the chat needs: no similarity scores or internals.
    return {
        "answer": result["answer"],
        "sources": [
            {"source": s["source"], "page": s["page"]}
            for s in result["sources"]
        ],
    }