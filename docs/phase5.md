# Phase 5 — persistent finance controller backbone

## Added
- SQLite data store.
- Common `financial_records` table for invoices, payments, settlements and bank transactions.
- Reconciliation case table.
- Reconciliation links.
- Exception queue.
- Audit event log.
- Webhook event store with event-id idempotency.
- HMAC signature verification for the local webhook harness.
- API overview and exception endpoints.
- Benchmark importer.

## Why SQLite first
For a hackathon prototype, SQLite gives us a real persistent data layer with zero infrastructure overhead. The schema is designed to migrate to Postgres later.

## Important boundary
The webhook endpoint stores events and normalized data. It does not itself declare accounting truth. Reconciliation remains a separate decision layer.

## Next
- Replace local HMAC harness with exact Razorpay webhook signature verification and secret configuration.
- Add Postgres option for deployment.
- Connect Phase 2/3 reconciliation decisions to `reconciliation_cases` and `reconciliation_links`.
- Add real batch-run endpoint.
