# ReconPilot — Finance Controller Starter Dataset

Generated on 2026-09-03 for a Razorpay Buildathon Track 04 prototype.

## Why these files look this way

Razorpay's settlement APIs expose settlement-level fields such as `id`, `amount`, `status`, `fees`, `tax`, `utr`, and timestamps. Its settlement report contains transaction-level fields such as `entity_id`, `type`, `debit`, `credit`, `amount`, `fee`, `tax`, `settlement_id`, `payment_id`, `settlement_utr`, `order_id`, and payment method metadata.

The dataset deliberately mirrors that shape, while the bank statement is represented separately because a merchant's bank statement is an external source that must be reconciled against the processor data.

## Files

- `invoices.csv` — 500 merchant invoices.
- `payments.csv` — payment records with clean, weak, missing and messy invoice references.
- `settlements.csv` — settlement batches.
- `settlement_lines.csv` — Razorpay-style settlement reconciliation rows.
- `razorpay_settlement_report_sample.csv` — same settlement-line data in a Razorpay-shaped export.
- `bank_statement.csv` — normalized bank transactions.
- `bank_format_a.csv` — one bank-style shape using a signed Amount column.
- `bank_format_b.csv` — another bank-style shape using Debit/Credit.
- `ground_truth_private.csv` — hidden evaluation mapping; do NOT upload this to the model.
- `reconciliation_engine.py` — baseline matching engine and evaluation output.

## Important

This is **synthetic**, not real customer financial data. It was generated from public Razorpay schemas and public examples of bank/reconciliation file structures.

That is intentional: for the buildathon benchmark, we need known ground truth so we can truthfully calculate match rate, precision, recall and exceptions.

## Deliberate anomalies included

- exact invoice/payment matches
- split/partial payments
- duplicate payment candidates
- missing invoice references
- spaces / punctuation changes in references
- settlement fees
- tax on fees
- settlement batches containing multiple payments
- bank UTR matching
- bank description formatting differences
- bank amount discrepancy
- unrelated bank credits
- bank fee debits
- manual settlement adjustments

## Product pipeline

1. Ingest and normalize each source.
2. Deterministic matching first.
3. AI/ML only for ambiguous entity resolution and exception reasoning.
4. Confidence gate.
5. Auto-close only above a strict threshold.
6. Send uncertain cases to an exception queue.
7. Store evidence + reason + model version + action in an audit trail.
8. Evaluate on `ground_truth_private.csv`, which the agent never sees.

## First demo

Run:

```bash
python reconciliation_engine.py
```

The output gives the baseline precision/recall and the number of automatically matched, AI-resolved and unresolved invoices.

