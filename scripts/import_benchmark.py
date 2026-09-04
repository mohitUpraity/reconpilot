
from pathlib import Path
import sys, csv
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from db.database import init_db
from db.repository import upsert_financial_record,audit

DATA=ROOT/"data"; MERCHANT="merchant_demo"

def read(name):
    with open(DATA/name,newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    init_db()
    for r in read("invoices.csv"):
        upsert_financial_record(MERCHANT,"merchant","INV:"+r["invoice_id"],"invoice",
            r["invoice_date"],int(r["amount"]),r["currency"],"receivable",
            r["customer_name"],r["invoice_id"],"Invoice",r)
    for r in read("payments.csv"):
        upsert_financial_record(MERCHANT,"payment",r["payment_id"],"payment",
            r["payment_date"],int(r["amount"]),r["currency"],"credit",
            r["customer_name"],r["invoice_reference"],r["description"],r)
    for r in read("settlements.csv"):
        upsert_financial_record(MERCHANT,"razorpay",r["settlement_id"],"settlement",
            r["settlement_date"],int(r["net_amount"]),r["currency"],"credit",
            "",r["utr"],"Settlement",r)
    for r in read("bank_statement.csv"):
        upsert_financial_record(MERCHANT,"bank",r["bank_txn_id"],"bank_transaction",
            r["transaction_date"],
            int(r["credit"]) if int(r["credit"]) else int(r["debit"]),
            "INR","credit" if int(r["credit"]) else "debit",
            "",r["reference"],r["description"],r)
    audit(MERCHANT,"BENCHMARK_IMPORTED","system:import",{
        "sources":["invoices.csv","payments.csv","settlements.csv","bank_statement.csv"]
    })
    print("Benchmark imported.")

if __name__=="__main__": main()
