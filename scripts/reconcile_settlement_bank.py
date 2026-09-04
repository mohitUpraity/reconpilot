from __future__ import annotations
from pathlib import Path
import json, re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from db.database import init_db, get_conn
from db.repository import list_records, create_case, create_link, create_exception, audit

MERCHANT="merchant_demo"

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def run():
    init_db()
    settlements=list_records(MERCHANT,"razorpay","settlement")
    banks=list_records(MERCHANT,"bank","bank_transaction")
    used=set(); results=[]
    for s in settlements:
        candidates=[]
        for b in banks:
            if b["record_id"] in used or b.get("direction")!="credit":
                continue
            utr_match=bool(s["reference"]) and norm(s["reference"]) == norm(b.get("reference"))
            amount_exact=int(s["amount"] or 0)==int(b["amount"] or 0)
            score=(0.80 if utr_match else 0)+(0.20 if amount_exact else 0)
            candidates.append((score,utr_match,amount_exact,b))
        candidates.sort(key=lambda x:x[0],reverse=True)
        if not candidates or candidates[0][0] < 1.0:
            status="UNRESOLVED"; conf=candidates[0][0] if candidates else 0; chosen=None
            reason="No bank credit matched both settlement UTR and net amount."
        else:
            status="RECONCILED"; conf=0.995; chosen=candidates[0][3]
            reason="Settlement UTR and net amount exactly match bank credit."
        cid=create_case(MERCHANT,"settlement_to_bank",status,conf,s["record_id"],chosen["record_id"] if chosen else None,
                        "settlement_bank_controller_v1",reason)
        if chosen:
            used.add(chosen["record_id"])
            create_link(cid,s["record_id"],chosen["record_id"],"settlement_bank",conf,"settlement_bank_controller_v1")
        else:
            create_exception(cid,"HIGH",reason)
        audit(MERCHANT,"SETTLEMENT_BANK_DECISION","system:settlement-controller",{
            "settlement_record_id":s["record_id"],"bank_record_id":chosen["record_id"] if chosen else None,
            "status":status,"confidence":conf
        },case_id=cid)
        results.append(status)
    summary={
        "settlements":len(settlements),
        "bank_transactions":len(banks),
        "reconciled":results.count("RECONCILED"),
        "unresolved":results.count("UNRESOLVED"),
        "match_rate":round(results.count("RECONCILED")/len(results),4) if results else 0,
        "unused_bank_credits":sum(1 for b in banks if b["record_id"] not in used and b.get("direction")=="credit")
    }
    (ROOT/"outputs"/"settlement_bank_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    return summary

if __name__=="__main__":run()
