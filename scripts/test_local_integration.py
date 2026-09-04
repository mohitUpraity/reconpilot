from pathlib import Path
import hashlib, hmac, json, os, sys, sqlite3
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ["RAZORPAY_WEBHOOK_SECRET"]="local-secret"
os.environ["MERCHANT_ID"]="merchant_demo"
from fastapi.testclient import TestClient
from api.app import app
from db.database import get_conn

client=TestClient(app)
body=json.dumps({"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_local_001","order_id":"ord_local_001","amount":250000,"currency":"INR","status":"captured","created_at":1788516000,"description":"local integration"}}}},separators=(",",":"))
sig=hmac.new(b"local-secret",body.encode(),hashlib.sha256).hexdigest()
headers={"X-Razorpay-Signature":sig,"X-Razorpay-Event-Id":"evt_local_001"}
r1=client.post("/webhooks/razorpay",content=body,headers=headers)
assert r1.status_code==200, r1.text
r2=client.post("/webhooks/razorpay",content=body,headers=headers)
assert r2.status_code==200 and r2.json()["status"]=="duplicate_ignored"
health=client.get("/health"); assert health.status_code==200
assert client.get("/").status_code==200
assert client.get("/web/app.js").status_code==200
assert client.get("/web/styles.css").status_code==200

conn=get_conn()
webhooks=conn.execute("SELECT COUNT(*) c FROM webhook_events WHERE merchant_id='merchant_demo'").fetchone()["c"]
pay=conn.execute("SELECT COUNT(*) c FROM financial_records WHERE record_id='razorpay:pay_local_001'").fetchone()["c"]
conn.close()
assert webhooks >= 1, webhooks
assert pay == 1, pay
print(json.dumps({"signature":"PASS","idempotency":"PASS","payment_normalization":"PASS","webhook_rows":webhooks,"normalized_payment_rows":pay}))
