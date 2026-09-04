# Phase 7 — DB-driven controller UI

Added a finance-control UI backed by the existing API/database.

Views:
- Overview: source counts, reconciliation health, exceptions, recent audit activity.
- Reconciliation: filterable persistent cases.
- Exceptions: review queue.
- Case detail: matched/unmatched records, confidence, evidence links, exception reason.
- Audit Trail: recent controller events.

The UI is intentionally lightweight (vanilla HTML/CSS/JS) so it can be replaced by React later without changing API contracts.
