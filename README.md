# ReconPilot — AI Finance Controller

Razorpay AI Buildathon — Track 04 prototype.

## Finance-ops loop
Invoice → Payment → Settlement → Bank

## Architecture
Data ingestion → normalization → deterministic matching → AI investigation → confidence/policy gate → reconciliation or exception → audit trail.

## Current implementation
- 500-invoice synthetic benchmark with known private ground truth.
- 1,188 normalized benchmark records.
- SQLite persistence for financial records, reconciliation cases, links, exceptions, audits and webhook events.
- DB-backed FastAPI dashboard.
- Razorpay Test Mode API adapter for payments, settlements and combined settlement reconciliation.
- Razorpay webhook raw-body HMAC verification and event-id idempotency.

## Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m db.database
python scripts/import_benchmark.py
python -m src.db_reconciliation
uvicorn api.app:app --reload --port 8000
```
Open http://127.0.0.1:8000

## Razorpay Test Mode
Copy `.env.example` to `.env` and add Test Mode credentials plus the webhook secret. Never commit secrets. `scripts/sync_razorpay_test.py` performs networked Test Mode reads; normal benchmark/demo flow does not require network access.

## Data/evaluation policy
`data/ground_truth_private.csv` is evaluation-only. It must never be passed to the model or exposed in the UI.

## Final readiness checklist

### Razorpay integration
- Payments and settlements use the Razorpay REST API adapter with pagination (100-record page size).
- Settlement recon uses `GET /v1/settlements/recon/combined` and supports up to 1000 records per request.
- Webhooks validate the raw request body with HMAC-SHA256 and use `X-Razorpay-Event-Id` for duplicate-event handling.
- Live Test Mode network execution is optional and requires credentials in `.env`; this artifact was not run against a merchant account in this environment.

### Benchmark integrity
- Synthetic benchmark: 500 invoices, 531 payments, 76 settlements, 543 settlement lines, 81 bank transactions.
- Private ground truth remains evaluation-only.
- Held-out offline controller benchmark: 96.61% precision, 75.00% recall, 84.44% F1 on the test split.
- These metrics are explicitly **not** presented as live-LLM performance.

### Verification
- `pytest -q`: 10 passed.
- Local webhook smoke test: signature validation, idempotency and payment normalization passed.
- Missing Razorpay credentials fail closed.
- Python compile check passed.
