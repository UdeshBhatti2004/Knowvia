import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.auth import require_user
from app.core import config
from app.main import app
from app.repositories import workspace_repository
from app.services import billing_service, usage_service

client = TestClient(app)

WEBHOOK_SECRET = "test_webhook_secret"


@pytest.fixture(autouse=True)
def fake_razorpay_config(monkeypatch):
    monkeypatch.setattr(config, "RAZORPAY_KEY_ID", "rzp_test_fake")
    monkeypatch.setattr(config, "RAZORPAY_KEY_SECRET", "fake_secret")
    monkeypatch.setattr(config, "RAZORPAY_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setattr(config, "RAZORPAY_PLAN_ID_STARTER", "plan_starter_fake")
    monkeypatch.setattr(config, "RAZORPAY_PLAN_ID_PRO", "plan_pro_fake")


def sign(body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def make_event(name, subscription_id="sub_1", plan_id="plan_pro_fake"):
    return {
        "event": name,
        "payload": {
            "subscription": {"entity": {"id": subscription_id, "plan_id": plan_id}}
        },
    }


def post_webhook(event, signature="auto"):
    body = json.dumps(event).encode()
    if signature == "auto":
        signature = sign(body)
    headers = {"x-razorpay-signature": signature} if signature else {}
    return client.post("/billing/webhook", content=body, headers=headers)


def make_workspace(plan=None, subscription_id="sub_1"):
    ws = workspace_repository.create_workspace("owner-1", "Shop")
    if plan:
        workspace_repository.set_plan(ws["_id"], plan)
    if subscription_id:
        workspace_repository.set_subscription(ws["_id"], subscription_id)
    return ws["_id"]


def plan_of(ws_id):
    return workspace_repository.get_by_id(ws_id)["plan"]


# ---- signature ----


def test_verify_signature_accepts_valid():
    body = b'{"a": 1}'
    assert billing_service.verify_signature(body, sign(body)) is True


def test_verify_signature_rejects_wrong_missing_and_tampered():
    body = b'{"a": 1}'
    assert billing_service.verify_signature(body, sign(body, "other")) is False
    assert billing_service.verify_signature(body, None) is False
    assert billing_service.verify_signature(body, "") is False
    assert billing_service.verify_signature(b'{"a": 2}', sign(body)) is False


def test_verify_signature_rejects_when_secret_not_configured(monkeypatch):
    monkeypatch.setattr(config, "RAZORPAY_WEBHOOK_SECRET", None)
    body = b"{}"
    assert billing_service.verify_signature(body, sign(body)) is False


# ---- webhook route ----


def test_webhook_rejects_bad_signature():
    ws_id = make_workspace()
    res = post_webhook(make_event("subscription.activated"), signature="bad")
    assert res.status_code == 400
    assert plan_of(ws_id) == "free"


def test_webhook_rejects_missing_signature():
    res = post_webhook(make_event("subscription.activated"), signature=None)
    assert res.status_code == 400


def test_webhook_rejects_invalid_json_even_if_signed():
    body = b"not json"
    res = client.post(
        "/billing/webhook",
        content=body,
        headers={"x-razorpay-signature": sign(body)},
    )
    assert res.status_code == 400


def test_webhook_activated_sets_pro():
    ws_id = make_workspace()
    res = post_webhook(make_event("subscription.activated", plan_id="plan_pro_fake"))
    assert res.status_code == 200
    assert plan_of(ws_id) == "pro"


def test_webhook_charged_sets_starter():
    ws_id = make_workspace()
    res = post_webhook(
        make_event("subscription.charged", plan_id="plan_starter_fake")
    )
    assert res.status_code == 200
    assert plan_of(ws_id) == "starter"


@pytest.mark.parametrize(
    "name",
    ["subscription.cancelled", "subscription.halted", "subscription.completed"],
)
def test_webhook_ended_events_set_free(name):
    ws_id = make_workspace(plan="pro")
    res = post_webhook(make_event(name))
    assert res.status_code == 200
    assert plan_of(ws_id) == "free"


def test_webhook_unknown_event_is_ignored():
    ws_id = make_workspace(plan="pro")
    res = post_webhook(make_event("payment.captured"))
    assert res.status_code == 200
    assert plan_of(ws_id) == "pro"


def test_webhook_unknown_subscription_is_ignored():
    ws_id = make_workspace(plan="pro")
    res = post_webhook(make_event("subscription.cancelled", subscription_id="sub_x"))
    assert res.status_code == 200
    assert plan_of(ws_id) == "pro"


def test_webhook_unknown_plan_id_leaves_plan_unchanged():
    ws_id = make_workspace()
    res = post_webhook(
        make_event("subscription.activated", plan_id="plan_unknown")
    )
    assert res.status_code == 200
    assert plan_of(ws_id) == "free"


def test_webhook_same_event_twice_gives_same_result():
    ws_id = make_workspace()
    event = make_event("subscription.activated", plan_id="plan_pro_fake")
    assert post_webhook(event).status_code == 200
    assert post_webhook(event).status_code == 200
    assert plan_of(ws_id) == "pro"


# ---- subscribe route ----


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.text = json.dumps(self._data)

    def json(self):
        return self._data


def login_as(ws_id):
    app.dependency_overrides[require_user] = lambda: ws_id


def test_subscribe_returns_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(config, "RAZORPAY_KEY_SECRET", None)
    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "pro"})
    assert res.status_code == 503


def test_subscribe_returns_503_when_plan_id_missing(monkeypatch):
    monkeypatch.setattr(config, "RAZORPAY_PLAN_ID_STARTER", None)
    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "starter"})
    assert res.status_code == 503


def test_subscribe_rejects_unknown_plan():
    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "gold"})
    assert res.status_code == 422


def test_subscribe_success_saves_subscription_id(monkeypatch):
    sent = {}

    def fake_post(url, **kwargs):
        sent["url"] = url
        sent["json"] = kwargs["json"]
        return FakeResponse(200, {"id": "sub_123"})

    monkeypatch.setattr(billing_service.httpx, "post", fake_post)

    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "pro"})

    assert res.status_code == 200
    assert res.json() == {"subscription_id": "sub_123", "key_id": "rzp_test_fake"}
    assert sent["json"]["plan_id"] == "plan_pro_fake"
    assert sent["json"]["notes"]["workspace_id"] == ws_id
    saved = workspace_repository.get_by_id(ws_id)
    assert saved["razorpay_subscription_id"] == "sub_123"
    # Paying is confirmed by the webhook, not by this call.
    assert saved["plan"] == "free"


def test_subscribe_returns_502_when_razorpay_errors(monkeypatch):
    monkeypatch.setattr(
        billing_service.httpx,
        "post",
        lambda url, **kw: FakeResponse(400, {"error": "bad"}),
    )
    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "pro"})
    assert res.status_code == 502


def test_subscribe_returns_502_when_network_fails(monkeypatch):
    def boom(url, **kw):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(billing_service.httpx, "post", boom)
    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "pro"})
    assert res.status_code == 502



# ---- double subscribe and cancel ----


def test_subscribe_blocked_when_already_on_paid_plan(monkeypatch):
    called = {"n": 0}

    def fake_post(url, **kwargs):
        called["n"] += 1
        return FakeResponse(200, {"id": "sub_new"})

    monkeypatch.setattr(billing_service.httpx, "post", fake_post)

    ws_id = make_workspace(plan="starter", subscription_id="sub_1")
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "pro"})

    assert res.status_code == 409
    assert called["n"] == 0
    assert plan_of(ws_id) == "starter"


def test_cancel_without_period_end_falls_back_to_free(monkeypatch):
    monkeypatch.setattr(
        billing_service.httpx,
        "post",
        lambda url, **kw: FakeResponse(200, {"id": "sub_1", "status": "cancelled"}),
    )

    ws_id = make_workspace(plan="pro", subscription_id="sub_1")
    login_as(ws_id)
    res = client.post("/billing/cancel")

    assert res.status_code == 200
    assert res.json()["plan_ends_at"] is None
    assert plan_of(ws_id) == "free"


def test_cancel_without_subscription_returns_404():
    ws_id = make_workspace(subscription_id=None)
    login_as(ws_id)
    res = client.post("/billing/cancel")
    assert res.status_code == 404


def test_cancel_on_free_plan_returns_404():
    ws_id = make_workspace(plan="free", subscription_id="sub_1")
    login_as(ws_id)
    res = client.post("/billing/cancel")
    assert res.status_code == 404


def test_cancel_returns_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(config, "RAZORPAY_KEY_SECRET", None)
    ws_id = make_workspace(plan="pro", subscription_id="sub_1")
    login_as(ws_id)
    res = client.post("/billing/cancel")
    assert res.status_code == 503


def test_cancel_razorpay_error_keeps_plan(monkeypatch):
    monkeypatch.setattr(
        billing_service.httpx,
        "post",
        lambda url, **kw: FakeResponse(400, {"error": "bad"}),
    )
    ws_id = make_workspace(plan="pro", subscription_id="sub_1")
    login_as(ws_id)
    res = client.post("/billing/cancel")
    assert res.status_code == 502
    assert plan_of(ws_id) == "pro"




# ---- cancel at period end ----


def iso_in(days):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_cancel_schedules_end_of_period(monkeypatch):
    ends = datetime.now(timezone.utc) + timedelta(days=20)
    sent = {}

    def fake_post(url, **kwargs):
        sent["url"] = url
        sent["json"] = kwargs["json"]
        return FakeResponse(
            200,
            {"id": "sub_1", "status": "active", "current_end": int(ends.timestamp())},
        )

    monkeypatch.setattr(billing_service.httpx, "post", fake_post)

    ws_id = make_workspace(plan="pro", subscription_id="sub_1")
    login_as(ws_id)
    res = client.post("/billing/cancel")

    expected = datetime.fromtimestamp(
        int(ends.timestamp()), tz=timezone.utc
    ).isoformat()

    assert res.status_code == 200
    assert sent["url"].endswith("/subscriptions/sub_1/cancel")
    assert sent["json"] == {"cancel_at_cycle_end": 1}
    assert res.json()["plan_ends_at"] == expected
    assert plan_of(ws_id) == "pro"
    assert workspace_repository.get_by_id(ws_id)["plan_ends_at"] == expected
    assert usage_service.get_plan_key(ws_id) == "pro"


def test_cancel_twice_does_not_call_razorpay_again(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, **kwargs):
        calls["n"] += 1
        return FakeResponse(
            200,
            {
                "id": "sub_1",
                "status": "active",
                "current_end": int((datetime.now(timezone.utc) + timedelta(days=9)).timestamp()),
            },
        )

    monkeypatch.setattr(billing_service.httpx, "post", fake_post)

    ws_id = make_workspace(plan="pro", subscription_id="sub_1")
    login_as(ws_id)
    first = client.post("/billing/cancel")
    second = client.post("/billing/cancel")

    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["plan_ends_at"] == second.json()["plan_ends_at"]
    assert calls["n"] == 1


def test_expired_plan_counts_as_free_and_future_stays_paid():
    past_id = make_workspace(plan="pro")
    workspace_repository.set_plan_ends_at(past_id, iso_in(-1))
    assert usage_service.get_plan_key(past_id) == "free"

    future_id = make_workspace(plan="pro")
    workspace_repository.set_plan_ends_at(future_id, iso_in(10))
    assert usage_service.get_plan_key(future_id) == "pro"


def test_webhook_cancelled_ignored_before_period_end():
    ws_id = make_workspace(plan="pro")
    workspace_repository.set_plan_ends_at(ws_id, iso_in(10))
    res = post_webhook(make_event("subscription.cancelled"))
    assert res.status_code == 200
    assert plan_of(ws_id) == "pro"


def test_webhook_cancelled_applies_after_period_end():
    ws_id = make_workspace(plan="pro")
    workspace_repository.set_plan_ends_at(ws_id, iso_in(-1))
    res = post_webhook(make_event("subscription.cancelled"))
    assert res.status_code == 200
    saved = workspace_repository.get_by_id(ws_id)
    assert saved["plan"] == "free"
    assert "plan_ends_at" not in saved


def test_webhook_halted_drops_plan_even_without_end_date():
    ws_id = make_workspace(plan="pro")
    res = post_webhook(make_event("subscription.halted"))
    assert res.status_code == 200
    assert plan_of(ws_id) == "free"


def test_webhook_activated_clears_scheduled_end():
    ws_id = make_workspace(plan="starter")
    workspace_repository.set_plan_ends_at(ws_id, iso_in(5))
    res = post_webhook(make_event("subscription.activated", plan_id="plan_pro_fake"))
    assert res.status_code == 200
    saved = workspace_repository.get_by_id(ws_id)
    assert saved["plan"] == "pro"
    assert "plan_ends_at" not in saved


def test_subscribe_allowed_after_paid_plan_expired(monkeypatch):
    monkeypatch.setattr(
        billing_service.httpx,
        "post",
        lambda url, **kw: FakeResponse(200, {"id": "sub_new"}),
    )
    ws_id = make_workspace(plan="pro", subscription_id="sub_old")
    workspace_repository.set_plan_ends_at(ws_id, iso_in(-1))
    login_as(ws_id)
    res = client.post("/billing/subscribe", json={"plan": "pro"})
    assert res.status_code == 200
    assert res.json()["subscription_id"] == "sub_new"


def test_usage_reports_plan_ends_at_only_when_set(monkeypatch):
    monkeypatch.setattr(usage_service, "count_documents", lambda w: 0)
    monkeypatch.setattr(usage_service, "count_questions_this_month", lambda w: 0)

    free_id = make_workspace(subscription_id=None)
    assert "plan_ends_at" not in usage_service.get_usage(free_id)

    paid_id = make_workspace(plan="pro")
    ends = iso_in(10)
    workspace_repository.set_plan_ends_at(paid_id, ends)
    assert usage_service.get_usage(paid_id)["plan_ends_at"] == ends
    