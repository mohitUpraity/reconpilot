
from __future__ import annotations
from pathlib import Path
import csv,json,os,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from db.database import init_db
from db.repository import list_records,list_cases
from scripts.run_ai_controller import build_packet
from ai.investigator import investigate

MERCHANT=os.getenv("MERCHANT_ID","merchant_demo")
OUT=ROOT/"outputs"

def main():
    init_db()
    invoices=list_records(MERCHANT,"merchant","invoice")
    payments=list_records(MERCHANT,"payment","payment")
    cases=list_cases(MERCHANT)

    # DB is the authoritative application state.
    baseline_by_invoice={}
    for c in cases:
        inv=(c.get("primary_record_id") or "").rsplit(":",1)[-1]
        matched=(c.get("matched_record_id") or "")
        pay=matched.rsplit(":",1)[-1] if matched else ""
        baseline_by_invoice[inv]={
            "payment_id":pay,
            "status":c["status"],
            "confidence":c["confidence"] or 0
        }

    hard=[i for i in invoices
          if baseline_by_invoice.get(i["record_id"].rsplit(":",1)[-1],{}).get("status")!="RECONCILED"]

    ai_rows=[]
    for inv in hard:
        packet=build_packet(inv,payments)
        result=investigate(packet,live=False)
        ai_rows.append({
            "invoice_id":inv["record_id"].rsplit(":",1)[-1],
            "decision":result["decision"],
            "selected_payment_id":result.get("selected_payment_id") or "",
            "confidence":result.get("confidence",0),
            "provider":result.get("provider","offline"),
            "model":result.get("model","evidence-policy-v1"),
            "evidence":json.dumps(result.get("evidence",[]),separators=(",",":")),
            "risks":json.dumps(result.get("risks",[]),separators=(",",":"))
        })

    OUT.mkdir(exist_ok=True)
    with open(OUT/"phase9_hard_cases_ai.csv","w",newline="",encoding="utf-8") as f:
        fields=list(ai_rows[0]) if ai_rows else [
            "invoice_id","decision","selected_payment_id","confidence",
            "provider","model","evidence","risks"
        ]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(ai_rows)

    final=[]
    for inv in invoices:
        inv_id=inv["record_id"].rsplit(":",1)[-1]
        b=baseline_by_invoice.get(inv_id,{
            "payment_id":"","status":"UNRESOLVED","confidence":0
        })
        if b["status"]=="RECONCILED":
            final.append({
                "invoice_id":inv_id,"payment_id":b["payment_id"],
                "source":"baseline","decision":"AUTO_MATCH",
                "confidence":b["confidence"]
            })
        else:
            a=next((x for x in ai_rows if x["invoice_id"]==inv_id),None)
            final.append({
                "invoice_id":inv_id,
                "payment_id":a["selected_payment_id"] if a and a["decision"]=="MATCH" else "",
                "source":"ai_investigator" if a else "baseline",
                "decision":a["decision"] if a else b["status"],
                "confidence:a":a["confidence"] if a else b["confidence"]
            })

    # normalize accidental key from construction
    for r in final:
        if "confidence:a" in r:
            r["confidence"]=r.pop("confidence:a")

    with open(OUT/"phase9_final_predictions.csv","w",newline="",encoding="utf-8") as f:
        fields=["invoice_id","payment_id","source","decision","confidence"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        w.writerows(final)

    print(json.dumps({
        "total_invoices":len(invoices),
        "baseline_reconciled":sum(v["status"]=="RECONCILED" for v in baseline_by_invoice.values()),
        "hard_cases_to_ai":len(hard),
        "ai_matches":sum(x["decision"]=="MATCH" for x in ai_rows),
        "ai_review":sum(x["decision"]=="REVIEW" for x in ai_rows),
        "ai_unresolved":sum(x["decision"]=="UNRESOLVED" for x in ai_rows),
        "final_predicted_matches":sum(bool(x["payment_id"]) for x in final)
    },indent=2))

if __name__=="__main__":
    main()
