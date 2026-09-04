# Razorpay Test Mode integration

## What this phase adds

ReconPilot can receive Razorpay webhook events in a FastAPI service, validate the webhook signature, deduplicate repeated events, and persist the raw event for downstream reconciliation.

## Why this architecture

Razorpay documents webhooks for payment and settlement events and recommends signature validation. Razorpay also calls out idempotency and webhook event ordering as important considerations. Settlement webhook payloads include settlement amount, fees, tax and UTR; Razorpay says UTR can be used to reconcile the settlement against the bank statement.

## Local setup

1. Create Razorpay **Test Mode** API keys.
2. Copy `.env.example` to `.env` and fill in the test keys and webhook secret.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start:

```bash
uvicorn app.main:app --reload --port 8000
```

5. Health check:

`GET http://localhost:8000/health`

## Webhook endpoint

`POST /webhooks/razorpay`

Use a public HTTPS endpoint (Razorpay webhook configuration requires an accessible webhook URL; for local development use a suitable tunnel that Razorpay permits).

## Event handling policy

- Verify `X-Razorpay-Signature` against the raw request body.
- Deduplicate using the event ID (or a body hash fallback).
- Persist raw payload before business processing.
- Treat webhook state as asynchronous; for critical confirmation, fetch the payment/order/settlement through the API.
- Never let a webhook directly mutate accounting truth without passing through the reconciliation and audit layers.
