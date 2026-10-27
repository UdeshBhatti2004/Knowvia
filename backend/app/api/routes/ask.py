
from fastapi import APIRouter, HTTPException

from backend.app.schemas.question import QuestionRequest
from backend.app.services.answer_service import generate_answer
from backend.app.services.knowledge_service import retrieve_knowledge


router = APIRouter()


@router.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        documents, _ = retrieve_knowledge(request.question)
    except Exception as exc:
        print(f"Document retrieval failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Document retrieval failed. Check the backend logs.",
        ) from exc

    if not documents:
        return {
            "question": request.question,
            "answer": (
                "Sorry, I couldn't find relevant information "
                "in the available documents."
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
        answer = generate_answer(request.question, context)
    except Exception as exc:
        print(f"Answer generation failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Please try again later.",
        ) from exc

    return {
        "question": request.question,
        "answer": answer,
        "source": best_document["source"],
        "page": best_document["page"],
        "similarity": round(best_score, 4),
        "sources": sources,
    }
