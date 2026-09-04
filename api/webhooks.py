from __future__ import annotations
import hashlib, hmac, json, os
from fastapi import APIRouter, Header, HTTPException, Request
from db.repository import save_webhook_event, upsert_financial_record, audit

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

def verify_razorpay_signature(raw_body: bytes, signature: str|None, secret: str|None=None) -> bool:
    if not signature:
        return False
    secret = secret or os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str|None = Header(default=None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str|None = Header(default=None, alias="X-Razorpay-Event-Id"),
):
    raw = await request.body()
    if not verify_razorpay_signature(raw, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid Razorpay webhook signature")
    if not x_razorpay_event_id:
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Event-Id")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    merchant_id = os.getenv("MERCHANT_ID", "merchant_demo")
    event_type = payload.get("event", "unknown")
    inserted = save_webhook_event(
        x_razorpay_event_id, merchant_id, "razorpay", event_type, True, payload
    )
    if not inserted:
        return {"status":"duplicate_ignored", "event_id":x_razorpay_event_id}

    entity = payload.get("payload",{}).get("payment",{}).get("entity",{})
    payment_id = entity.get("id")
    if payment_id:
        upsert_financial_record(
            merchant_id, "razorpay", payment_id, "payment",
            entity.get("created_at"), entity.get("amount"), entity.get("currency","INR"),
            "credit", entity.get("email",""), entity.get("order_id",""),
            entity.get("description",""), entity
        )
    audit(merchant_id, "RAZORPAY_WEBHOOK_ACCEPTED", "system:razorpay-webhook", {
        "event_id":x_razorpay_event_id, "event_type":event_type, "payment_id":payment_id
    })
    return {"status":"accepted", "event_id":x_razorpay_event_id, "event_type":event_type}
