
from __future__ import annotations
from pathlib import Path
import csv,json,sqlite3

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"; OUT=ROOT/"outputs"; DB=ROOT/"db"/"reconpilot.db"

def read(p):
    with open(p,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def score(pred,truth):
    gt={r["invoice_id"]:r["payment_id"]
        for r in truth if r.get("relationship")=="invoice_payment" and r.get("payment_id")}
    tp=fp=fn=0
    for r in pred:
        e=gt.get(r["invoice_id"],""); p=r.get("payment_id","")
        if p and p==e: tp+=1
        elif p: fp+=1
        elif e: fn+=1
    precision=tp/(tp+fp) if tp+fp else 0
    recall=tp/(tp+fn) if tp+fn else 0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0
    return {"cases":len(pred),"truth_cases":len(gt),"tp":tp,"fp":fp,"fn":fn,
            "precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4)}

def baseline_from_db():
    conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
    rows=conn.execute("""
        SELECT primary_record_id,matched_record_id,status
        FROM reconciliation_cases
        WHERE merchant_id='merchant_demo' AND case_type='invoice_to_payment'
    """).fetchall()
    conn.close()
    out=[]
    for r in rows:
        inv=(r["primary_record_id"] or "").rsplit(":",1)[-1]
        pid=(r["matched_record_id"] or "")
        pay=pid.rsplit(":",1)[-1] if pid else ""
        out.append({"invoice_id":inv,"payment_id":pay})
    return out

def main():
    truth=read(DATA/"ground_truth_private.csv")
    final=read(OUT/"phase9_final_predictions.csv")
    baseline=baseline_from_db()
    b=score(baseline,truth)
    f=score(final,truth)
    comparison={"baseline_db":b,"phase9":f,
                "delta":{
                    "precision":round(f["precision"]-b["precision"],4),
                    "recall":round(f["recall"]-b["recall"],4),
                    "f1":round(f["f1"]-b["f1"],4)
                }}
    OUT.joinpath("phase9_comparison.json").write_text(json.dumps(comparison,indent=2),encoding="utf-8")
    print(json.dumps(comparison,indent=2))

if __name__=="__main__": main()
