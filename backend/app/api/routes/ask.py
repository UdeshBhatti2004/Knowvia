from fastapi import APIRouter, HTTPException
import time
from app.schemas.question import QuestionRequest
from app.services.answer_service import AnswerQuotaExceeded, generate_answer
from app.services.knowledge_service import retrieve_knowledge
from app.schemas.assistant import DEFAULT_FALLBACK_MESSAGE
from app.services.assistant_service import get_assistant_settings


router = APIRouter()


def _fallback_message() -> str:
    # A broken settings file must never break /ask, so fall back to the default.
    try:
        return get_assistant_settings().fallback_message
    except Exception as exc:
        print(f"Could not load assistant settings: {exc}")
        return DEFAULT_FALLBACK_MESSAGE


@router.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        started = time.perf_counter()
        documents, _ = retrieve_knowledge(request.question)
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
            "answer": _fallback_message(),
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
        answer = _fallback_message()

    return {
        "question": request.question,
        "answer": answer,
        "source": best_document["source"],
        "page": best_document["page"],
        "similarity": round(best_score, 4),
        "sources": sources,
    }