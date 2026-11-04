import pytest
from fastapi import HTTPException

from app.repositories import workspace_repository
from app.services import usage_service


def make_workspace(plan=None):
    ws = workspace_repository.create_workspace("owner-1", "Shop")
    if plan:
        workspace_repository.set_plan(ws["_id"], plan)
    return ws["_id"]


def test_new_workspace_is_free():
    ws_id = make_workspace()
    assert usage_service.get_plan_key(ws_id) == "free"


def test_unknown_workspace_falls_back_to_free():
    assert usage_service.get_plan_key("does-not-exist") == "free"


def test_unknown_plan_value_falls_back_to_free():
    ws_id = make_workspace("gold")
    assert usage_service.get_plan_key(ws_id) == "free"


def test_pro_has_higher_limits_than_free():
    free_id = make_workspace()
    free = usage_service.get_limits(free_id)
    pro_ws = workspace_repository.create_workspace("owner-2", "Pro Shop")
    workspace_repository.set_plan(pro_ws["_id"], "pro")
    pro = usage_service.get_limits(pro_ws["_id"])
    assert pro["max_documents"] > free["max_documents"]
    assert pro["max_questions_per_month"] > free["max_questions_per_month"]


def test_get_usage_reports_plan(monkeypatch):
    monkeypatch.setattr(usage_service, "count_documents", lambda w: 1)
    monkeypatch.setattr(
        usage_service, "count_questions_this_month", lambda w: 2
    )
    ws_id = make_workspace("pro")
    usage = usage_service.get_usage(ws_id)
    assert usage["plan"] == "pro"
    assert usage["plan_name"] == "Pro"
    assert usage["documents"] == 1
    assert usage["questions"] == 2


def test_free_upload_blocked_at_limit_but_pro_allowed(monkeypatch):
    monkeypatch.setattr(usage_service, "count_documents", lambda w: 5)

    free_id = make_workspace()
    with pytest.raises(HTTPException) as exc:
        usage_service.check_can_upload(free_id)
    assert exc.value.status_code == 403
    assert "Free plan limit reached" in exc.value.detail

    pro_ws = workspace_repository.create_workspace("owner-2", "Pro Shop")
    workspace_repository.set_plan(pro_ws["_id"], "pro")
    usage_service.check_can_upload(pro_ws["_id"])  # no error


def test_free_questions_blocked_at_limit_but_pro_allowed(monkeypatch):
    monkeypatch.setattr(
        usage_service, "count_questions_this_month", lambda w: 200
    )

    free_id = make_workspace()
    with pytest.raises(HTTPException) as exc:
        usage_service.check_can_ask(free_id)
    assert exc.value.status_code == 429

    pro_ws = workspace_repository.create_workspace("owner-2", "Pro Shop")
    workspace_repository.set_plan(pro_ws["_id"], "pro")
    usage_service.check_can_ask(pro_ws["_id"])  # no error