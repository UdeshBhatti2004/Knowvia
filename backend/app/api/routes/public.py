from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from app.api.client_ip import get_client_ip

from app.api.routes.ask import ask_question
from app.core.config import PUBLIC_RATE_LIMITS
from app.schemas.question import QuestionRequest
from app.services.assistant_service import get_assistant_settings
from app.services.rate_limiter import RateLimiter
from app.services.widget_service import is_valid_key

limiter = RateLimiter(PUBLIC_RATE_LIMITS)


def require_widget_key(x_widget_key: str | None = Header(default=None)) -> None:
    if not x_widget_key or not is_valid_key(x_widget_key):
        raise HTTPException(status_code=401, detail="Invalid widget key.")


def enforce_rate_limit(request: Request) -> None:
    ip = get_client_ip(request)
    wait = limiter.check(ip)

    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many questions. Please wait a moment and try again.",
            headers={"Retry-After": str(wait)},
        )


router = APIRouter(
    prefix="/public",
    dependencies=[Depends(require_widget_key)],
)


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
def public_assistant_route():
    settings = get_assistant_settings()
    return {
        "name": settings.name,
        "welcome_message": settings.welcome_message,
    }


@router.post(
    "/ask",
    response_model=PublicAnswer,
    dependencies=[Depends(enforce_rate_limit)],
)
def public_ask_route(body: PublicQuestion):
    # Same retrieval and answer logic as the dashboard /ask.
    result = ask_question(QuestionRequest(question=body.question))

    # Only what the chat needs: no similarity scores or internals.
    return {
        "answer": result["answer"],
        "sources": [
            {"source": s["source"], "page": s["page"]}
            for s in result["sources"]
        ],
    }