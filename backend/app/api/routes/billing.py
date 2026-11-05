import asyncio
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.auth import require_user
from app.services import billing_service

router = APIRouter(prefix="/billing")


class SubscribeRequest(BaseModel):
    plan: Literal["starter", "pro"]


@router.post("/subscribe")
def subscribe_route(
    payload: SubscribeRequest, workspace_id: str = Depends(require_user)
):
    try:
        return billing_service.create_subscription(workspace_id, payload.plan)
    except billing_service.BillingNotConfigured:
        raise HTTPException(status_code=503, detail="Billing is not configured.")
    except billing_service.AlreadySubscribed:
        raise HTTPException(
            status_code=409,
            detail="You already have a paid plan. Cancel it first.",
        )
    except billing_service.BillingError:
        raise HTTPException(
            status_code=502,
            detail="Could not start the subscription. Try again.",
        )


@router.post("/cancel")
def cancel_route(workspace_id: str = Depends(require_user)):
    try:
        ends_at = billing_service.cancel_subscription(workspace_id)
    except billing_service.BillingNotConfigured:
        raise HTTPException(status_code=503, detail="Billing is not configured.")
    except billing_service.NoSubscription:
        raise HTTPException(status_code=404, detail="No active subscription.")
    except billing_service.BillingError:
        raise HTTPException(
            status_code=502,
            detail="Could not cancel the subscription. Try again.",
        )

    return {"ok": True, "plan_ends_at": ends_at}


@router.post("/webhook")
async def webhook_route(request: Request):
    # Open route: protected by the Razorpay signature, not a login token.
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")

    if not billing_service.verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature.")

    try:
        event = json.loads(body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload.")

    try:
        await asyncio.to_thread(billing_service.handle_event, event)
    except Exception as exc:
        # 500 makes Razorpay retry later.
        print(f"Webhook handling failed: {exc}")
        raise HTTPException(status_code=500, detail="Could not process event.")

    return {"ok": True}