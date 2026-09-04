
from __future__ import annotations
from pathlib import Path
import json
from difflib import SequenceMatcher
from .common import norm_ref, norm_name, date_distance
from db.database import init_db
from db.repository import (
    list_records, create_case, create_link, create_exception,
    audit, clear_reconciliation_results
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_MERCHANT="merchant_demo"

def sim(a,b):
    return SequenceMatcher(None,norm_name(a),norm_name(b)).ratio()

def reconcile_one(invoice,payments,used):
    candidates=[]
    for p in payments:
        ia=int(invoice["amount"] or 0); pa=int(p["amount"] or 0)
        amount_ratio=max(0.0,1-abs(ia-pa)/max(ia,1))
        inv_ref=norm_ref(invoice["reference"]); pay_ref=norm_ref(p["reference"])
        exact=bool(inv_ref) and inv_ref==pay_ref
        partial=bool(inv_ref and pay_ref and inv_ref in pay_ref)
        ns=sim(invoice["customer_name"],p["customer_name"])
        dd=date_distance(invoice["event_date"],p["event_date"])
        ds=1.0 if dd<=7 else (.8 if dd<=15 else (.5 if dd<=45 else 0.0))
        ref_score=1.0 if exact else (.7 if partial else 0.0)
        score=.45*ref_score+.30*amount_ratio+.15*ns+.10*ds
        candidates.append((score,p,exact,amount_ratio,ns,dd))
    candidates.sort(key=lambda x:x[0],reverse=True)

    if not candidates:
        return "UNRESOLVED",0,None,"No payment candidates."

    best=candidates[0]; second=candidates[1] if len(candidates)>1 else None
    score,p,exact,amount_ratio,ns,dd=best
    margin=score-(second[0] if second else 0)

    if p["record_id"] in used:
        return "REVIEW",round(score,4),None,"Best candidate is already allocated to another invoice."
    if exact and amount_ratio>=.999:
        return "RECONCILED",.995,p,"Exact normalized invoice reference and exact amount."
    if score>=.88 and margin>=.12:
        return "RECONCILED",round(min(.97,score+.03),4),p,"High-confidence multi-signal relationship."
    if score>=.70:
        return "REVIEW",round(score,4),None,"Plausible candidate but evidence is insufficient for automatic close."
    return "UNRESOLVED",round(score,4),None,"Insufficient evidence to safely reconcile."

def run(merchant_id=DEFAULT_MERCHANT):
    init_db()
    clear_reconciliation_results(merchant_id)
    invoices=list_records(merchant_id,"merchant","invoice")
    payments=list_records(merchant_id,"payment","payment")
    used=set(); results=[]

    for inv in invoices:
        status,conf,selected,reason=reconcile_one(inv,payments,used)
        cid=create_case(
            merchant_id,"invoice_to_payment",status,conf,
            inv["record_id"],selected["record_id"] if selected else None,
            "db_reconciliation_v2",reason
        )
        if selected:
            used.add(selected["record_id"])
            create_link(cid,inv["record_id"],selected["record_id"],
                        "invoice_payment",conf,"db_reconciliation_v2")
        else:
            create_exception(cid,"HIGH" if status=="UNRESOLVED" else "MEDIUM",reason)
        audit(merchant_id,"RECONCILIATION_DECISION","system:reconciliation",{
            "invoice_record_id":inv["record_id"],
            "payment_record_id":selected["record_id"] if selected else None,
            "status":status,"confidence":conf
        },case_id=cid)
        results.append(status)

    summary={
        "merchant_id":merchant_id,
        "invoice_cases":len(results),
        "reconciled":results.count("RECONCILED"),
        "review":results.count("REVIEW"),
        "unresolved":results.count("UNRESOLVED"),
        "auto_reconciled_rate":round(results.count("RECONCILED")/len(results),4) if results else 0
    }
    (ROOT/"outputs"/"db_reconciliation_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    return summary

if __name__=="__main__":
    run()
