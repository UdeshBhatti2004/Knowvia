import hashlib
import hmac
from datetime import datetime, timezone

import httpx

from app.core import config
from app.repositories import workspace_repository
from app.services import usage_service

RAZORPAY_API = "https://api.razorpay.com/v1"

# Number of billing cycles Razorpay will charge (120 months = 10 years).
SUBSCRIPTION_CYCLES = 120

ACTIVE_EVENTS = {"subscription.activated", "subscription.charged"}
ENDED_EVENTS = {
    "subscription.cancelled",
    "subscription.halted",
    "subscription.completed",
}


class BillingNotConfigured(Exception):
    pass


class BillingError(Exception):
    pass


class AlreadySubscribed(Exception):
    pass


class NoSubscription(Exception):
    pass


def _razorpay_plan_ids() -> dict:
    return {
        "starter": config.RAZORPAY_PLAN_ID_STARTER,
        "pro": config.RAZORPAY_PLAN_ID_PRO,
    }


def plan_key_for_razorpay_id(razorpay_plan_id: str | None) -> str | None:
    """Map a Razorpay plan_... id back to our plan key (starter / pro)."""
    for key, rid in _razorpay_plan_ids().items():
        if rid and rid == razorpay_plan_id:
            return key
    return None


def create_subscription(workspace_id: str, plan_key: str) -> dict:
    """Create a Razorpay subscription and remember its id on the workspace."""
    razorpay_plan_id = _razorpay_plan_ids().get(plan_key)

    if (
        not config.RAZORPAY_KEY_ID
        or not config.RAZORPAY_KEY_SECRET
        or not razorpay_plan_id
    ):
        raise BillingNotConfigured()

    if usage_service.get_plan_key(workspace_id) != config.DEFAULT_PLAN:
        raise AlreadySubscribed()

    try:
        response = httpx.post(
            f"{RAZORPAY_API}/subscriptions",
            auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET),
            json={
                "plan_id": razorpay_plan_id,
                "total_count": SUBSCRIPTION_CYCLES,
                "customer_notify": 1,
                "notes": {"workspace_id": workspace_id, "plan": plan_key},
            },
            timeout=15,
        )
    except httpx.HTTPError as exc:
        print(f"Razorpay request failed: {exc}")
        raise BillingError() from exc

    if response.status_code >= 400:
        print(f"Razorpay error {response.status_code}: {response.text}")
        raise BillingError()

    subscription_id = response.json().get("id")
    if not subscription_id:
        raise BillingError()

    workspace_repository.set_subscription(workspace_id, subscription_id)

    return {
        "subscription_id": subscription_id,
        "key_id": config.RAZORPAY_KEY_ID,
    }


def cancel_subscription(workspace_id: str) -> str | None:
    """Cancel at the end of the paid period. Returns the end date (ISO).

    The plan stays active until then. If Razorpay gives no period end, the
    plan drops to free right away (returns None).
    """
    if not config.RAZORPAY_KEY_ID or not config.RAZORPAY_KEY_SECRET:
        raise BillingNotConfigured()

    workspace = workspace_repository.get_by_id(workspace_id)
    subscription_id = (workspace or {}).get("razorpay_subscription_id")

    if (
        not subscription_id
        or usage_service.get_plan_key(workspace_id) == config.DEFAULT_PLAN
    ):
        raise NoSubscription()

    # Already scheduled: answer again with the same date, no second call.
    already = (workspace or {}).get("plan_ends_at")
    if already:
        return already

    try:
        response = httpx.post(
            f"{RAZORPAY_API}/subscriptions/{subscription_id}/cancel",
            auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET),
            json={"cancel_at_cycle_end": 1},
            timeout=15,
        )
    except httpx.HTTPError as exc:
        print(f"Razorpay cancel request failed: {exc}")
        raise BillingError() from exc

    if response.status_code >= 400:
        print(f"Razorpay cancel error {response.status_code}: {response.text}")
        raise BillingError()

    current_end = response.json().get("current_end")
    if not current_end:
        workspace_repository.set_plan(workspace_id, config.DEFAULT_PLAN)
        return None

    ends_at = datetime.fromtimestamp(int(current_end), tz=timezone.utc).isoformat()
    workspace_repository.set_plan_ends_at(workspace_id, ends_at)
    return ends_at


def verify_signature(body: bytes, signature: str | None) -> bool:
    """Check the webhook came from Razorpay (HMAC SHA256 of the raw body)."""
    if not config.RAZORPAY_WEBHOOK_SECRET or not signature:
        return False

    expected = hmac.new(
        config.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def handle_event(event: dict) -> None:
    """Apply a verified webhook event. Safe to run twice for the same event."""
    name = event.get("event")
    if name not in ACTIVE_EVENTS and name not in ENDED_EVENTS:
        return

    subscription = (
        ((event.get("payload") or {}).get("subscription") or {}).get("entity")
        or {}
    )
    subscription_id = subscription.get("id")
    if not subscription_id:
        return

    workspace = workspace_repository.get_by_subscription_id(subscription_id)
    if not workspace:
        print(f"Webhook for unknown subscription: {subscription_id}")
        return

    if name in ACTIVE_EVENTS:
        plan_key = plan_key_for_razorpay_id(subscription.get("plan_id"))
        if not plan_key:
            print(f"Webhook with unknown plan id: {subscription.get('plan_id')}")
            return
        workspace_repository.set_plan(workspace["_id"], plan_key)
    else:
        # A scheduled cancel keeps the plan until the paid period ends.
        # usage_service drops it to free once plan_ends_at has passed.
        if (
            workspace.get("plan_ends_at")
            and usage_service.get_plan_key(workspace["_id"]) != config.DEFAULT_PLAN
        ):
            return
        workspace_repository.set_plan(workspace["_id"], config.DEFAULT_PLAN)