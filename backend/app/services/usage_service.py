from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import FREE_MAX_DOCUMENTS, FREE_MAX_QUESTIONS_PER_MONTH
from app.repositories import conversation_repository
from app.repositories.source_repository import load_sources_metadata


def _month_start_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()


def count_documents(workspace_id: str) -> int:
    metadata = load_sources_metadata(workspace_id)
    return sum(1 for r in metadata.values() if r.get("status") != "Failed")


def count_questions_this_month(workspace_id: str) -> int:
    return conversation_repository.count_since(
        workspace_id, _month_start_iso()
    )


def get_usage(workspace_id: str) -> dict:
    return {
        "documents": count_documents(workspace_id),
        "documents_limit": FREE_MAX_DOCUMENTS,
        "questions": count_questions_this_month(workspace_id),
        "questions_limit": FREE_MAX_QUESTIONS_PER_MONTH,
    }


def check_can_upload(workspace_id: str) -> None:
    if count_documents(workspace_id) >= FREE_MAX_DOCUMENTS:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Free plan limit reached: {FREE_MAX_DOCUMENTS} documents. "
                "Delete a document to upload a new one."
            ),
        )


def check_can_ask(workspace_id: str) -> None:
    # Fail open: a broken counter must never block customers.
    try:
        used = count_questions_this_month(workspace_id)
    except Exception as exc:
        print(f"Could not count questions: {exc}")
        return

    if used >= FREE_MAX_QUESTIONS_PER_MONTH:
        raise HTTPException(
            status_code=429,
            detail=(
                "This assistant has reached its monthly question limit. "
                "Please contact the business directly."
            ),
        )