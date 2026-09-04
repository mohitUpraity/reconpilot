from __future__ import annotations
from pathlib import Path
import os, sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from integrations.razorpay_client import RazorpayClient
from db.database import init_db
from db.repository import upsert_financial_record, audit

def main():
    init_db()
    merchant=os.getenv("MERCHANT_ID","merchant_demo")
    client=RazorpayClient()
    payments=client.fetch_all_payments()
    for p in payments:
        upsert_financial_record(merchant,"razorpay",p["id"],"payment",p.get("created_at"),
            p.get("amount"),p.get("currency","INR"),"credit",p.get("email",""),
            p.get("order_id",""),p.get("description",""),p)
    settlements=client.fetch_all_settlements()
    for s in settlements:
        upsert_financial_record(merchant,"razorpay",s["id"],"settlement",s.get("created_at"),
            s.get("amount"),s.get("currency","INR"),"credit","",s.get("utr",""),
            "Razorpay settlement",s)
    audit(merchant,"RAZORPAY_TEST_SYNC","system:razorpay-sync",
          {"payments":len(payments),"settlements":len(settlements)})
    print(json.dumps({"payments_synced":len(payments),"settlements_synced":len(settlements)},indent=2))
if __name__=="__main__": main()
