import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.api.client_ip import get_client_ip
from app.api.routes.ask import OFF_TOPIC_MESSAGE, ask_question
from app.core.config import PUBLIC_RATE_LIMITS
from app.knowledge.workspace_loader import ensure_loaded
from app.repositories import conversation_repository
from app.schemas.question import QuestionRequest
from app.services.assistant_service import get_assistant_settings
from app.services.rate_limiter import RateLimiter
from app.services.usage_service import check_can_ask
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


def _outcome(answer: str, sources: list) -> str:
    if answer == OFF_TOPIC_MESSAGE:
        return "off_topic"
    if not sources:
        return "not_found"
    return "answered"


def _log(workspace_id: str, question: str, answer: str, sources: list) -> None:
    # Never let logging break the customer's answer.
    try:
        conversation_repository.log_conversation(
            workspace_id,
            question,
            answer,
            _outcome(answer, sources),
            [s["source"] for s in sources],
        )
    except Exception as exc:
        print(f"Could not log conversation: {exc}")


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
    # Monthly plan limit, checked before any Gemini call.
    await asyncio.to_thread(check_can_ask, workspace_id)

    await asyncio.to_thread(ensure_loaded, workspace_id)

    # Same retrieval and answer logic as the dashboard /ask.
    result = await asyncio.to_thread(
        ask_question, QuestionRequest(question=body.question), workspace_id
    )

    sources = [
        {"source": s["source"], "page": s["page"]} for s in result["sources"]
    ]

    await asyncio.to_thread(
        _log, workspace_id, body.question, result["answer"], sources
    )

    # Only what the chat needs: no similarity scores or internals.
    return {"answer": result["answer"], "sources": sources}