
from __future__ import annotations
from pathlib import Path
import sys,csv,json,os

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from db.database import init_db
from db.repository import list_records, list_cases, create_case, create_link, create_exception, audit
from ai.investigator import investigate

MERCHANT=os.getenv("MERCHANT_ID","merchant_demo")

def sim(a,b):
    from difflib import SequenceMatcher
    from src.common import norm_name
    return SequenceMatcher(None,norm_name(a),norm_name(b)).ratio()

def build_packet(inv,payments,top_n=5):
    from src.common import norm_ref, date_distance
    items=[]
    inv_ref=norm_ref(inv["reference"])
    for p in payments:
        inv_amt=int(inv["amount"] or 0); p_amt=int(p["amount"] or 0)
        ratio=max(0,1-abs(inv_amt-p_amt)/max(inv_amt,1))
        pref=norm_ref(p["reference"])
        exact=bool(inv_ref and inv_ref==pref)
        partial=bool(inv_ref and pref and inv_ref in pref)
        cs=sim(inv["customer_name"],p["customer_name"])
        dd=date_distance(inv["event_date"],p["event_date"])
        rs=1 if exact else (.7 if partial else 0)
        score=.45*rs+.30*ratio+.15*cs+.10*(1 if dd<=7 else (.8 if dd<=15 else (.5 if dd<=45 else 0)))
        items.append({
            "payment_id":p["record_id"].split(":",1)[-1],
            "amount":p["amount"],
            "payment_date":p["event_date"],
            "invoice_reference":p["reference"],
            "customer_name":p["customer_name"],
            "description":p["description"],
            "score":round(score,4),
            "signals":{
                "reference_exact":exact,
                "reference_partial":partial,
                "amount_exact":inv_amt==p_amt,
                "amount_ratio":round(ratio,4),
                "customer_similarity":round(cs,4),
                "date_distance_days":dd
            }
        })
    items.sort(key=lambda x:x["score"],reverse=True)
    return {
        "case_id":inv["record_id"].rsplit(":",1)[-1],
        "invoice":{
            "invoice_id":inv["record_id"].rsplit(":",1)[-1],
            "customer_name":inv["customer_name"],
            "invoice_date":inv["event_date"],
            "amount":int(inv["amount"] or 0),
            "currency":inv["currency"]
        },
        "candidates":items[:top_n],
        "constraints":{
            "allowed_decisions":["MATCH","REVIEW","UNRESOLVED"],
            "never_invent_payment_id":True,
            "do_not_use_ground_truth":True
        }
    }

def main():
    init_db()
    invoices=list_records(MERCHANT,"merchant","invoice")
    payments=list_records(MERCHANT,"payment","payment")

    # Investigate every invoice in a reproducible batch; in production we'd usually
    # send only REVIEW candidates to the LLM to control cost and latency.
    outputs=[]
    for inv in invoices:
        packet=build_packet(inv,payments)
        result=investigate(packet)
        outputs.append({
            "invoice_id":inv["record_id"].rsplit(":",1)[-1],
            **result
        })

    out=ROOT/"outputs"
    out.mkdir(exist_ok=True)
    with open(out/"phase9_ai_controller_results.csv","w",newline="",encoding="utf-8") as f:
        fields=["invoice_id","decision","selected_payment_id","confidence","provider","model","evidence","risks"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in outputs:
            w.writerow({
                **{k:r.get(k,"") for k in fields[:5]},
                "model":r.get("model",""),
                "evidence":json.dumps(r.get("evidence",[]),separators=(",",":")),
                "risks":json.dumps(r.get("risks",[]),separators=(",",":"))
            })

    print(json.dumps({
        "cases":len(outputs),
        "match":sum(x["decision"]=="MATCH" for x in outputs),
        "review":sum(x["decision"]=="REVIEW" for x in outputs),
        "unresolved":sum(x["decision"]=="UNRESOLVED" for x in outputs),
        "provider_counts":{
            p:sum(x["provider"]==p for x in outputs)
            for p in sorted(set(x["provider"] for x in outputs))
        }
    },indent=2))

if __name__=="__main__":
    main()
