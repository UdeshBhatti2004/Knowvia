from fastapi import APIRouter, Depends, HTTPException
import time

from app.api.auth import require_user
from app.knowledge.workspace_loader import ensure_loaded
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID
from app.schemas.question import QuestionRequest
from app.services.answer_service import AnswerQuotaExceeded, generate_answer
from app.services.knowledge_service import retrieve_knowledge
from app.schemas.assistant import DEFAULT_FALLBACK_MESSAGE
from app.services.assistant_service import get_assistant_settings


router = APIRouter()


def _fallback_message(workspace_id: str = DEFAULT_WORKSPACE_ID) -> str:
    # Broken settings must never break /ask, so fall back to the default.
    try:
        return get_assistant_settings(workspace_id).fallback_message
    except Exception as exc:
        print(f"Could not load assistant settings: {exc}")
        return DEFAULT_FALLBACK_MESSAGE


@router.post("/ask")
def ask_endpoint(
    request: QuestionRequest, workspace_id: str = Depends(require_user)
):
    ensure_loaded(workspace_id)
    return ask_question(request, workspace_id)


def ask_question(request: QuestionRequest, workspace_id: str = DEFAULT_WORKSPACE_ID):
    try:
        started = time.perf_counter()
        if workspace_id == DEFAULT_WORKSPACE_ID:
            documents, _ = retrieve_knowledge(request.question)
        else:
            documents, _ = retrieve_knowledge(
                request.question, workspace_id=workspace_id
            )
        print(f"[timing] retrieval: {time.perf_counter() - started:.2f}s")
    except Exception as exc:
        print(f"Document retrieval failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Document retrieval failed. Check the backend logs.",
        ) from exc

    if not documents:
        return {
            "question": request.question,
            "answer": _fallback_message(workspace_id),
            "source": None,
            "page": None,
            "similarity": None,
            "sources": [],
        }

    best_document, best_score = documents[0]

    unique_sources = {}

    for doc, chunk_score in documents:
        key = (doc["source"], doc["page"])

        if key not in unique_sources:
            unique_sources[key] = {
                "source": doc["source"],
                "page": doc["page"],
                "similarity": round(chunk_score, 4),
            }

    sources = list(unique_sources.values())

    context = "\n\n".join(
        doc["text"] for doc, _ in documents
    )

    try:
        started = time.perf_counter()
        answer = generate_answer(request.question, context)
        print(f"[timing] answer generation: {time.perf_counter() - started:.2f}s")
    except AnswerQuotaExceeded as exc:
        print(f"Answer limit reached: {exc}")
        raise HTTPException(
            status_code=429,
            detail=(
                "The daily answer limit has been reached. "
                "Please try again later."
            ),
        ) from exc
    except Exception as exc:
        print(f"Answer generation failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Please try again later.",
        ) from exc

    # The model is told to use this exact sentence when the context has no
    # answer. Swap it for the saved fallback.
    if answer.strip() == DEFAULT_FALLBACK_MESSAGE:
        answer = _fallback_message(workspace_id)

    return {
        "question": request.question,
        "answer": answer,
        "source": best_document["source"],
        "page": best_document["page"],
        "similarity": round(best_score, 4),
        "sources": sources,
    }