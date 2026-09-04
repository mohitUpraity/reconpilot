from __future__ import annotations
from pathlib import Path
import csv, json, sqlite3, hashlib

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"; OUT=ROOT/"outputs"; DB=ROOT/"db"/"reconpilot.db"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def truth_map(rows):
    return {
        r["invoice_id"]: r["payment_id"]
        for r in rows
        if r.get("relationship") == "invoice_payment" and r.get("payment_id")
    }


def split(invoice_ids):
    buckets={"train":[],"validation":[],"test":[]}
    # Deterministic 60/20/20 split, independent of prediction outcomes.
    for inv in sorted(invoice_ids):
        n=int(hashlib.sha256(inv.encode()).hexdigest(),16) % 100
        buckets["train" if n < 60 else "validation" if n < 80 else "test"].append(inv)
    return buckets


def score(pred, truth, ids, auto_only=True):
    gt={i:truth[i] for i in ids if i in truth}
    pred_map={r["invoice_id"]: r for r in pred if r["invoice_id"] in ids}
    tp=fp=fn=0
    for inv in ids:
        expected=gt.get(inv, "")
        actual=pred_map.get(inv, {}).get("selected_payment_id", "") if auto_only else pred_map.get(inv, {}).get("selected_payment_id", "")
        if actual and actual == expected: tp += 1
        elif actual: fp += 1
        elif expected: fn += 1
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {"cases":len(ids),"truth_cases":len(gt),"tp":tp,"fp":fp,"fn":fn,
            "precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4)}


def apply_gate(rows, threshold):
    out=[]
    for r in rows:
        x=dict(r)
        if x.get("decision") != "MATCH" or float(x.get("confidence") or 0) < threshold:
            x["selected_payment_id"]=""
        out.append(x)
    return out


def main():
    truth=truth_map(read_csv(DATA/"ground_truth_private.csv"))
    pred=read_csv(OUT/"phase9_ai_controller_results.csv")
    for r in pred:
        r["invoice_id"] = r["invoice_id"].rsplit(":",1)[-1]
    ids=[r["invoice_id"] for r in pred]
    splits=split(ids)

    # Calibrate the auto-match confidence gate on validation only.
    candidates=[round(x/100,2) for x in range(50,100)]
    trials=[]
    for t in candidates:
        m=score(apply_gate(pred,t),truth,splits["validation"])
        trials.append((m["f1"],m["precision"],m["recall"],t,m))
    # Prefer highest F1, breaking ties toward higher precision.
    trials.sort(reverse=True, key=lambda x:(x[0],x[1]))
    best=trials[0]
    threshold=best[3]

    gated=apply_gate(pred,threshold)
    results={
        "split_counts":{k:len(v) for k,v in splits.items()},
        "calibration":{
            "source":"validation",
            "confidence_threshold":threshold,
            "validation_metrics":best[4]
        },
        "test_metrics":score(gated,truth,splits["test"]),
        "all_data_metrics":score(gated,truth,ids),
        "method":"deterministic offline investigator + calibrated controller gate",
        "warning":"This is an offline policy benchmark, not a live LLM evaluation."
    }
    OUT.joinpath("phase10_evaluation.json").write_text(json.dumps(results,indent=2),encoding="utf-8")

    with open(OUT/"phase10_test_predictions.csv","w",newline="",encoding="utf-8") as f:
        fields=["invoice_id","decision","selected_payment_id","confidence","provider","model","evidence","risks"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in gated:
            w.writerow({k:r.get(k,"") for k in fields})

    print(json.dumps(results,indent=2))

if __name__=="__main__": main()
