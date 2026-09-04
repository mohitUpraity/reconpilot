# Phase 9.5–12 — Safety gate, evaluation, human review, end-to-end reconciliation

## Phase 9.5: structured AI output safety
The live investigator now uses a Pydantic `ReconciliationDecision` contract after the Responses API Structured Output layer.

Validation layers:
1. OpenAI Structured Outputs enforces the JSON schema.
2. Pydantic rejects malformed data, extra fields, invalid confidence, and inconsistent decision/payment combinations.
3. Application policy checks that a selected payment ID is present in the evidence packet.
4. The controller remains the accounting authority; the model cannot write financial records directly.

Live API failures fail closed to `REVIEW`.

## Phase 10: held-out evaluation and confidence calibration
A deterministic SHA-256 split creates 60% train / 20% validation / 20% test partitions. The auto-match confidence threshold is chosen on validation only and then evaluated once on the held-out test set.

Current offline-policy benchmark:
- Validation threshold: 0.93
- Validation: 97.62% precision, 84.54% recall, 90.61% F1
- Held-out test: 96.61% precision, 75.00% recall, 84.44% F1

These are offline deterministic-controller metrics, not live-LLM metrics.

## Phase 11: human review workflow
`POST /api/v1/cases/{case_id}/resolve` supports:
- `approve_match` + payment ID
- `reject`

Human actions are atomic, update the case, close open exceptions, create the reconciliation link where applicable, and append an audit event.

## Phase 12: end-to-end finance loop
The database now persists three relationship stages:

`Invoice → Payment → Razorpay Settlement → Bank`

Current synthetic benchmark:
- Payment → Settlement: 531/531 reconciled
- Settlement → Bank: 74/76 reconciled; 2 unresolved
- Complete 4-hop chain from reconciled invoice cases to bank: 379 chains

The 2 unresolved settlement-to-bank cases and 5 unused bank credits remain visible as exceptions rather than being force-matched.
