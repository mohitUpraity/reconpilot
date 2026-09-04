from __future__ import annotations
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from db.database import init_db
from db.repository import list_records, create_case, create_link, create_exception, audit

MERCHANT="merchant_demo"

def read(name):
    with open(ROOT/"data"/name,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def run():
    init_db()
    payments=list_records(MERCHANT,"payment","payment")
    settlements={r["source_record_id"]:r for r in list_records(MERCHANT,"razorpay","settlement")}
    lines=read("settlement_lines.csv")
    by_payment={}
    for line in lines:
        pid=line.get("payment_id") or line.get("entity_id")
        sid=line.get("settlement_id")
        if pid and sid:
            by_payment.setdefault(pid,[]).append(line)
    results=[]
    for p in payments:
        pid=p["source_record_id"]
        matches=by_payment.get(pid,[])
        valid=[m for m in matches if m.get("settlement_id") in settlements and m.get("settled","False").lower()=="true"]
        chosen=valid[0] if len(valid)==1 else None
        if chosen:
            s=settlements[chosen["settlement_id"]]
            status="RECONCILED"; conf=.995; reason="Payment appears once in the settled Razorpay settlement lines."
            sid=s["record_id"]
        elif len(valid)>1:
            status="REVIEW"; conf=.5; reason="Payment maps to multiple settled settlement lines."; sid=None
        else:
            status="UNRESOLVED"; conf=0; reason="No unique settled Razorpay settlement line found for payment."; sid=None
        cid=create_case(MERCHANT,"payment_to_settlement",status,conf,p["record_id"],sid,
                        "payment_settlement_controller_v1",reason)
        if sid:
            create_link(cid,p["record_id"],sid,"payment_settlement",conf,"payment_settlement_controller_v1")
        else:
            create_exception(cid,"HIGH" if status=="UNRESOLVED" else "MEDIUM",reason)
        audit(MERCHANT,"PAYMENT_SETTLEMENT_DECISION","system:settlement-controller",{
            "payment_record_id":p["record_id"],"settlement_record_id":sid,"status":status,"confidence":conf
        },case_id=cid)
        results.append(status)
    summary={"payments":len(payments),"reconciled":results.count("RECONCILED"),"review":results.count("REVIEW"),"unresolved":results.count("UNRESOLVED"),
             "match_rate":round(results.count("RECONCILED")/len(results),4) if results else 0}
    (ROOT/"outputs"/"payment_settlement_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    return summary

if __name__=="__main__":run()
