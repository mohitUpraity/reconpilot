from pathlib import Path
import hashlib,hmac,json,os,sys,sqlite3
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['RAZORPAY_WEBHOOK_SECRET']='local-secret'
os.environ['MERCHANT_ID']='merchant_demo'
from db.database import init_db
from scripts.import_benchmark import main as import_benchmark
from src.db_reconciliation import run as reconcile
from fastapi.testclient import TestClient
from api.app import app

init_db()
import_benchmark()
reconcile('merchant_demo')
client=TestClient(app)
assert client.get('/health').status_code==200
assert client.get('/').status_code==200
assert client.get('/web/app.js').status_code==200
assert client.get('/web/styles.css').status_code==200
j=client.get('/api/v1/dashboard/merchant_demo').json()
for k in ('record_total','counts','sources','case_status','recent_activity'): assert k in j
assert j['record_total'] >= 1188
# signed webhook
payload={"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_phase8_smoke","order_id":"ord_phase8_smoke","amount":12345,"currency":"INR","status":"captured","created_at":1788516000}}}}
raw=json.dumps(payload,separators=(',',':'))
sig=hmac.new(b'local-secret',raw.encode(),hashlib.sha256).hexdigest()
h={'X-Razorpay-Signature':sig,'X-Razorpay-Event-Id':'evt_phase8_smoke'}
r1=client.post('/webhooks/razorpay',content=raw,headers=h); assert r1.status_code==200,r1.text
r2=client.post('/webhooks/razorpay',content=raw,headers=h); assert r2.status_code==200 and r2.json()['status']=='duplicate_ignored'
conn=sqlite3.connect(ROOT/'db'/'reconpilot.db')
conn.row_factory=sqlite3.Row
report={
'records':conn.execute("SELECT COUNT(*) c FROM financial_records WHERE merchant_id='merchant_demo'").fetchone()['c'],
'cases':conn.execute("SELECT COUNT(*) c FROM reconciliation_cases WHERE merchant_id='merchant_demo'").fetchone()['c'],
'links':conn.execute("SELECT COUNT(*) c FROM reconciliation_links").fetchone()['c'],
'exceptions':conn.execute("SELECT COUNT(*) c FROM exceptions e JOIN reconciliation_cases c ON c.case_id=e.case_id WHERE c.merchant_id='merchant_demo'").fetchone()['c'],
'audit':conn.execute("SELECT COUNT(*) c FROM audit_events WHERE merchant_id='merchant_demo'").fetchone()['c'],
'webhooks':conn.execute("SELECT COUNT(*) c FROM webhook_events WHERE merchant_id='merchant_demo'").fetchone()['c'],
}
conn.close()
print(json.dumps(report,indent=2))
