# Phase 8 — Razorpay Test Mode integration

Current Razorpay documentation used for this phase:
- Test Mode has separate API keys and simulated transactions.
- Payment and settlement APIs are available through the REST API.
- Combined settlement reconciliation is available at `/v1/settlements/recon/combined`.
- Webhook signatures use `X-Razorpay-Signature` and must be verified using the raw request body.
- `X-Razorpay-Event-Id` is used to recognize duplicate webhook deliveries.
- Webhook ordering should not be assumed.

Implemented:
1. Razorpay client for Test Mode payments, settlements and settlement-recon retrieval.
2. Raw-body signature verification.
3. Event-id idempotency.
4. Payment webhook normalization into the persistent financial-record store.
5. Test-mode pull sync script.

No Live Mode keys are required or used.
