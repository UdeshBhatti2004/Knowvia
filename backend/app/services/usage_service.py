from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import DEFAULT_PLAN, PLANS
from app.repositories import conversation_repository, workspace_repository
from app.repositories.source_repository import load_sources_metadata


def _month_start_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()


def _is_past(iso: str | None) -> bool:
    if not iso:
        return False
    try:
        moment = datetime.fromisoformat(iso)
    except ValueError:
        return False
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment <= datetime.now(timezone.utc)


def get_plan_ends_at(workspace_id: str) -> str | None:
    try:
        doc = workspace_repository.get_by_id(workspace_id)
    except Exception as exc:
        print(f"Could not read plan end date: {exc}")
        return None
    return (doc or {}).get("plan_ends_at")


def get_plan_key(workspace_id: str) -> str:
    """The workspace's plan. Falls back to the default if missing or unknown."""
    try:
        doc = workspace_repository.get_by_id(workspace_id)
    except Exception as exc:
        print(f"Could not read plan: {exc}")
        return DEFAULT_PLAN

    plan = (doc or {}).get("plan")
    if plan not in PLANS:
        return DEFAULT_PLAN
    if _is_past((doc or {}).get("plan_ends_at")):
        return DEFAULT_PLAN
    return plan


def get_limits(workspace_id: str) -> dict:
    return PLANS[get_plan_key(workspace_id)]


def count_documents(workspace_id: str) -> int:
    metadata = load_sources_metadata(workspace_id)
    return sum(1 for r in metadata.values() if r.get("status") != "Failed")


def count_questions_this_month(workspace_id: str) -> int:
    return conversation_repository.count_since(
        workspace_id, _month_start_iso()
    )


def get_usage(workspace_id: str) -> dict:
    plan_key = get_plan_key(workspace_id)
    plan = PLANS[plan_key]
    usage = {
        "plan": plan_key,
        "plan_name": plan["name"],
        "documents": count_documents(workspace_id),
        "documents_limit": plan["max_documents"],
        "questions": count_questions_this_month(workspace_id),
        "questions_limit": plan["max_questions_per_month"],
    }

    if plan_key != DEFAULT_PLAN:
        ends_at = get_plan_ends_at(workspace_id)
        if ends_at:
            usage["plan_ends_at"] = ends_at

    return usage


def check_can_upload(workspace_id: str) -> None:
    plan = get_limits(workspace_id)
    limit = plan["max_documents"]

    if count_documents(workspace_id) >= limit:
        raise HTTPException(
            status_code=403,
            detail=(
                f"{plan['name']} plan limit reached: {limit} documents. "
                "Delete a document to upload a new one."
            ),
        )


def check_can_ask(workspace_id: str) -> None:
    # Fail open: a broken counter must never block customers.
    try:
        used = count_questions_this_month(workspace_id)
        limit = get_limits(workspace_id)["max_questions_per_month"]
    except Exception as exc:
        print(f"Could not count questions: {exc}")
        return

    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                "This assistant has reached its monthly question limit. "
                "Please contact the business directly."
            ),
        )