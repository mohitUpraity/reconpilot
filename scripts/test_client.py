from __future__ import annotations
import os, json, hmac, hashlib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1]/".env")

secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
payload = {
    "id": "evt_demo_001",
    "event": "settlement.processed",
    "payload": {
        "settlement": {
            "entity": {
                "id": "setl_demo_001",
                "amount": 150000,
                "status": "processed",
                "fees": 3000,
                "tax": 540,
                "utr": "DEMO-UTR-001"
            }
        }
    }
}
raw = json.dumps(payload, separators=(",", ":")).encode()
sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
print("X-Razorpay-Signature:", sig)
print(raw.decode())
