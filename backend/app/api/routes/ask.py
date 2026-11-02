from fastapi import APIRouter, Depends, HTTPException
import time

from app.api.auth import require_user
from app.knowledge.workspace_loader import ensure_loaded
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID
from app.schemas.question import QuestionRequest
from app.services.answer_service import (
    OFF_TOPIC_MARKER,
    AnswerQuotaExceeded,
    generate_answer,
)
from app.services.knowledge_service import retrieve_knowledge
from app.schemas.assistant import DEFAULT_FALLBACK_MESSAGE
from app.services.assistant_service import get_assistant_settings
from app.repositories import workspace_repository


router = APIRouter()

OFF_TOPIC_MESSAGE = (
    "I'm this business's assistant, so I can only help with questions about it. "
    "Try asking about our fees, timings, policies or services."
)


def _fallback_message(workspace_id: str = DEFAULT_WORKSPACE_ID) -> str:
    # Broken settings must never break /ask, so fall back to the default.
    try:
        return get_assistant_settings(workspace_id).fallback_message
    except Exception as exc:
        print(f"Could not load assistant settings: {exc}")
        return DEFAULT_FALLBACK_MESSAGE


def _record_test(workspace_id: str) -> None:
    # Never let this break /ask.
    try:
        workspace_repository.mark_tested(workspace_id)
    except Exception as exc:
        print(f"Could not record test time: {exc}")


@router.post("/ask")
def ask_endpoint(
    request: QuestionRequest, workspace_id: str = Depends(require_user)
):
    ensure_loaded(workspace_id)
    result = ask_question(request, workspace_id)
    # Only reached when the ask succeeded (errors raise before this).
    _record_test(workspace_id)
    return result

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
        # Nothing matched. Let the model tell off-topic from missing info.
        try:
            probe = generate_answer(request.question, "")
        except Exception as exc:
            print(f"No-context answer failed: {exc}")
            probe = ""

        return {
            "question": request.question,
            "answer": (
                OFF_TOPIC_MESSAGE
                if OFF_TOPIC_MARKER in probe
                else _fallback_message(workspace_id)
            ),
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

    # Not a business question: clear message, no sources.
    if OFF_TOPIC_MARKER in answer:
        return {
            "question": request.question,
            "answer": OFF_TOPIC_MESSAGE,
            "source": None,
            "page": None,
            "similarity": None,
            "sources": [],
        }

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