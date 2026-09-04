from pathlib import Path
import csv, math, re
from datetime import datetime
from difflib import SequenceMatcher

BASE = Path(__file__).resolve().parent

def read_csv(name):
    with open(BASE/name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def norm_ref(s):
    s = (s or "").upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s

def norm_name(s):
    s = (s or "").upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s

def close_amount(a,b,tol=1):
    return abs(int(a)-int(b)) <= tol

invoices = read_csv("invoices.csv")
payments = read_csv("payments.csv")
settlements = read_csv("settlements.csv")
settlement_lines = read_csv("settlement_lines.csv")
bank = read_csv("bank_statement.csv")
truth = read_csv("ground_truth_private.csv")

# 1) Invoice -> payment matching.
# Deterministic first, then fuzzy/name/date/amount scoring.
payment_by_ref = {}
for p in payments:
    r = norm_ref(p.get("invoice_reference"))
    if r:
        payment_by_ref.setdefault(r, []).append(p)

pred_ip = []
used_payments = set()

for inv in invoices:
    candidates = []
    ref = norm_ref(inv["invoice_id"])
    candidates.extend(payment_by_ref.get(ref, []))
    if not candidates:
        for p in payments:
            score = 0
            if close_amount(inv["amount"], p["amount"]): score += 0.65
            days = abs((datetime.strptime(inv["invoice_date"],"%Y-%m-%d") -
                        datetime.strptime(p["payment_date"],"%Y-%m-%d")).days)
            if days <= 45: score += 0.15
            name_sim = SequenceMatcher(None, norm_name(inv["customer_name"]), norm_name(p["customer_name"])).ratio()
            score += 0.20 * name_sim
            if score >= 0.78:
                candidates.append((score,p))
        candidates = [x[1] if isinstance(x, tuple) else x for x in sorted(
            [(0.99 if norm_ref(inv["invoice_id"]) == norm_ref(x.get("invoice_reference")) else 0.0, x) for x in candidates],
            key=lambda z:z[0], reverse=True
        )]

    # Prefer exact reference matches; don't auto-close obvious duplicates.
    chosen = None
    for p in candidates:
        if p["payment_id"] not in used_payments:
            chosen = p
            break
    if chosen:
        confidence = 1.0 if norm_ref(inv["invoice_id"]) == norm_ref(chosen.get("invoice_reference")) and close_amount(inv["amount"],chosen["amount"]) else 0.86
        action = "AUTO_MATCH" if confidence >= 0.95 else "AI_MATCH"
        pred_ip.append([inv["invoice_id"], chosen["payment_id"], confidence, action])
        used_payments.add(chosen["payment_id"])
    else:
        pred_ip.append([inv["invoice_id"], "", 0.0, "UNRESOLVED"])

# 2) Payment -> settlement line matching.
settle_by_payment = {x["payment_id"]: x for x in settlement_lines if x.get("type")=="payment" and x.get("payment_id")}
pred_ps = []
for p in payments:
    line = settle_by_payment.get(p["payment_id"])
    if line:
        pred_ps.append([p["payment_id"], line["settlement_id"], 1.0])
    else:
        pred_ps.append([p["payment_id"], "", 0.0])

# 3) Settlement -> bank matching using UTR, then amount/date window.
pred_sb = []
for s in settlements:
    matches = [b for b in bank if norm_ref(b.get("reference")) == norm_ref(s["utr"])]
    if matches:
        b = matches[0]
        # Bank credit may have a deliberate discrepancy.
        conf = 1.0 if close_amount(s["net_amount"], b["credit"], tol=1) else 0.70
        pred_sb.append([s["settlement_id"], b["bank_txn_id"], conf, "UTR"])
        continue
    # fallback: amount/date
    best = None
    best_score = 0
    sd = datetime.strptime(s["settlement_date"],"%Y-%m-%d").date()
    for b in bank:
        bd = datetime.strptime(b["transaction_date"],"%Y-%m-%d").date()
        days = abs((sd-bd).days)
        if days > 2 or int(b["credit"]) == 0:
            continue
        amount_score = max(0, 1 - abs(int(s["net_amount"])-int(b["credit"])) / max(int(s["net_amount"]),1))
        score = 0.7*amount_score + 0.3*(1 if days==0 else 0.5)
        if score > best_score:
            best_score = score; best = b
    if best and best_score >= 0.80:
        pred_sb.append([s["settlement_id"], best["bank_txn_id"], best_score, "AMOUNT_DATE"])
    else:
        pred_sb.append([s["settlement_id"], "", 0.0, "UNRESOLVED"])

# Print honest summary.
invoice_by_pay = {t["payment_id"]: t["invoice_id"] for t in truth if t["relationship"]=="invoice_payment"}

tp = fp = fn = 0
for inv_id, pay_id, conf, action in pred_ip:
    truth_pay = next((t["payment_id"] for t in truth if t["invoice_id"]==inv_id and t["relationship"]=="invoice_payment"), "")
    if pay_id == truth_pay:
        tp += 1
    elif pay_id:
        fp += 1
    elif truth_pay:
        fn += 1

precision = tp/(tp+fp) if tp+fp else 0
recall = tp/(tp+fn) if tp+fn else 0

print("=== ReconPilot baseline reconciliation ===")
print(f"Invoices: {len(invoices)}")
print(f"Payments: {len(payments)}")
print(f"Settlement lines: {len(settlement_lines)}")
print(f"Settlements: {len(settlements)}")
print(f"Bank transactions: {len(bank)}")
print(f"Invoice→payment precision: {precision:.3f}")
print(f"Invoice→payment recall:    {recall:.3f}")
print(f"Invoice→payment TP/FP/FN:   {tp}/{fp}/{fn}")

auto = sum(1 for r in pred_ip if r[3]=="AUTO_MATCH")
ai = sum(1 for r in pred_ip if r[3]=="AI_MATCH")
unres = sum(1 for r in pred_ip if r[3]=="UNRESOLVED")
print(f"Auto-matched invoices: {auto}")
print(f"AI-resolved invoices: {ai}")
print(f"Unresolved invoices: {unres}")

sb_unres = sum(1 for r in pred_sb if not r[1])
print(f"Unresolved settlement→bank cases: {sb_unres}")
