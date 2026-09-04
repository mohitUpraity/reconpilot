
from __future__ import annotations
from pathlib import Path
import sys
import hmac,hashlib,json,subprocess,sys,urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def sign(obj, secret="DEMO_WEBHOOK_SECRET"):
    raw=json.dumps(obj,separators=(",",":")).encode()
    return hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest()

print("1) Initialize DB")
subprocess.run([sys.executable,"-m","db.database"],cwd=ROOT,check=True)

print("2) Import benchmark")
subprocess.run([sys.executable,"scripts/import_benchmark.py"],cwd=ROOT,check=True)

print("3) Database check")
from db.database import get_conn
conn=get_conn()
row=conn.execute("SELECT COUNT(*) AS c FROM financial_records WHERE merchant_id='merchant_demo'").fetchone()
print("financial_records:",row["c"])
conn.close()

print("4) Webhook endpoint must be run separately:")
print("   uvicorn api.app:app --reload --port 8000")
print("5) Then POST a signed test event to /webhooks/razorpay.")
