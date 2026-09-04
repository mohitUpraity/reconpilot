# ReconPilot — AI Finance Controller

> **Razorpay AI Buildathon 2026 | Track 04 — AI Finance Controller**
>
> *"Run the books and the cash position."*
> *Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic data,
> reporting its match rate and the exceptions it could not resolve.*
> — [razorpay.com/buildathon](https://razorpay.com/buildathon/)

---

## Quick Start (For Judges)

```bash
git clone <repo> && cd reconpilot_phase14_final
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add GEMINI_API_KEY
python -m db.database && python scripts/import_benchmark.py
python -m src.db_reconciliation
uvicorn api.app:app --reload --port 8000
# Open http://127.0.0.1:8000
```

```bash
pytest -q                       # 10 passed
```

---

## Table of Contents

1. [PS-4 Requirements and How We Meet Them](#ps-4-requirements-and-how-we-meet-them)
2. [The Problem — Why This Matters](#the-problem--why-this-matters)
3. [The Solution — ReconPilot](#the-solution--reconpilot)
4. [Live Demo Numbers (Real SQLite)](#live-demo-numbers)
5. [System Architecture](#system-architecture)
6. [Data Flow Diagrams (DFD)](#data-flow-diagrams)
7. [Three-Tier AI Engine](#three-tier-ai-engine)
8. [Razorpay Integration](#razorpay-integration)
9. [AI Governance — Triple Gate](#ai-governance--triple-gate)
10. [Benchmark and Accuracy](#benchmark-and-accuracy)
11. [Exception List (Honest Reporting)](#exception-list)
12. [What Broke at 2 AM](#what-broke-at-2-am)
13. [Database Schema](#database-schema)
14. [API Reference (17 Endpoints)](#api-reference)
15. [Project Structure](#project-structure)
16. [Environment Variables](#environment-variables)
17. [Verification Checklist](#verification-checklist)
18. [Judging Matrix — How We Score](#judging-matrix)

---

## PS-4 Requirements and How We Meet Them

The official problem statement for Track 04 states:

> **"Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic data,
> reporting its match rate and the exceptions it could not resolve."**
>
> **The bar:** *Throughput plus measured accuracy plus an honest exception list.
> One cherry-picked match proves nothing.*

| PS-4 Requirement | ReconPilot Implementation | Where to Verify |
|---|---|---|
| **"Closes one finance-ops loop"** | Full Invoice -> Payment -> Settlement -> Bank reconciliation pipeline | `/api/v1/chain/{id}` |
| **"50+ record batch"** | **500 invoices**, 531 payments, 76 settlements, 81 bank entries (10x the requirement) | `/api/v1/overview/merchant_demo` |
| **"Match rate"** | 389/500 auto-reconciled (77.8%), 96.61% precision on held-out test | `/api/v1/benchmark` |
| **"Exceptions it could not resolve"** | **111 exceptions** in live queue, 38 UNRESOLVED, 73 REVIEW | `/api/v1/exceptions/merchant_demo` |
| **"Throughput"** | Tier 1 <10ms, Tier 3 ~1.2s/case, full cycle <2min | SSE stream at `/api/v1/demo/stream` |
| **"Measured accuracy"** | Held-out test split: P=96.61%, R=75.00%, F1=84.44% | Benchmark tab in UI |
| **"Honest exception list"** | 111 cases with severity, reason, case_type, confidence score | Exception Queue in UI |

### Cross-Reference to Other Tracks

ReconPilot naturally intersects with other buildathon tracks:

| Track | How ReconPilot Touches It |
|---|---|
| **Track 01** (AI Growth) | Reconciliation health directly impacts merchant settlement confidence and revenue |
| **Track 02** (AI Risk) | Anomaly detection via exception flagging — disputed amounts, fee mismatches, silent gaps |
| **Track 03** (Revenue Recovery) | Unresolved cases surface revenue that has NOT landed — 38 unpaid invoices identified |
| **Track 04** (Finance Controller) | **PRIMARY TRACK** — full reconciliation loop with audit trail |

---

## The Problem — Why This Matters

> *"Reconciliation, settlement and forecasting are still done by hand."*
> — Razorpay Buildathon, Track 04 "Why now"

Every month-end, a merchant's finance team faces this:

```
+-------------------+     +-------------------+     +-------------------+     +-------------------+
|  500 INVOICES     |     |  531 PAYMENTS     |     |  76 SETTLEMENTS   |     |  81 BANK CREDITS  |
|  (Merchant ERP)   |     |  (Razorpay PG)    |     |  (Razorpay Settle)|     |  (Bank Statement) |
|                   |     |                   |     |                   |     |                   |
|  "Where did the   |     |  "Which invoice   |     |  "Why is the net  |     |  "Did every       |
|   money go?"      |     |   does this pay?" |     |   amount lower?"  |     |   settlement land?"|
+-------------------+     +-------------------+     +-------------------+     +-------------------+
```

**What breaks in practice:**

1. **Reference Drift** — Invoice `INV-2024-0142` paid as order `order_NX9k3`. No string match exists.
2. **Fee Erosion** — Invoice Rs.42,800. Settlement Rs.42,419. Razorpay deducted Rs.312 fee + Rs.69 GST.
3. **Silent Gaps** — 38 invoices had zero payment activity. Nobody noticed until the quarterly audit.
4. **Zero Governance** — A manual spreadsheet match has no audit trail, no policy gate, no undo.

**The cost:** 4-8 hours, 2 analysts, 3+ errors per month-end cycle.

---

## The Solution — ReconPilot

ReconPilot is a **production-grade AI Finance Controller** that autonomously closes the finance-ops loop:

```
Invoice --> Payment --> Settlement --> Bank
   |            |            |            |
   +-------- RECONCILED --------+         |
   |            |                         |
   +------ EXCEPTION QUEUE -----+         |
   |                                      |
   +---------- AUDIT TRAIL -------+-------+
```

**What makes it different from a demo stub:**

- **Not a chatbot wrapper** — deterministic matching handles 77.8% of cases at zero AI cost
- **Not one cherry-picked match** — processes 500 invoices in batch, reports match rate AND exceptions
- **Not AI-for-everything** — uses AI only for the 111 ambiguous cases (22.2%) where rules fail
- **Not a black box** — every decision has: evidence, confidence, policy gate, audit log, and a human queue

---

## Live Demo Numbers

> All numbers are live SQLite queries against `db/reconpilot.db`, never hardcoded.

| Metric | Count | Source |
|---|---|---|
| Financial Records | **1,655** | 4 sources normalized into unified schema |
| Invoices | 500 | Merchant ERP |
| Payments | 531 | Razorpay Test Mode format |
| Settlements | 76 headers + 543 lines | Razorpay combined settlement recon format |
| Bank Credits | 81 | Bank statement CSV |
| Reconciliation Cases | **1,031** | Invoice + settlement + bank matching |
| RECONCILED (auto) | **389** | Tier 1 deterministic engine |
| REVIEW (human queue) | **73** | Needs analyst decision |
| UNRESOLVED | **38** | No matching payment found |
| Exceptions | **111** | Cases where evidence was insufficient or conflicting |
| Audit Events | **1,100+** | Every decision, import, and override logged |
| Webhook Events | **4** | HMAC-verified Razorpay webhooks |

---

## System Architecture

```
+=====================================================================+
|                    ReconPilot Control Room (UI)                       |
|                 http://127.0.0.1:8000                                |
|         Vanilla JS + SSE Streaming + Real-time DB Binding            |
+===========================+=========================================+
                            |
               +------------v--------------+
               |     FastAPI Backend        |
               |     api/app.py (17 REST)   |
               |     api/webhooks.py (HMAC) |
               +------+------------+-------+
                      |            |
          +-----------v--+    +----v-------------------+
          |  SQLite DB   |    |  Razorpay Adapter      |
          |  7 Tables    |    |  integrations/         |
          |  FK Enforced |    |  razorpay_client.py    |
          |  3 Indexes   |    |  - Payments API        |
          +-----------+--+    |  - Settlements API     |
                      |       |  - Combined Recon API  |
                      |       |  - Webhook Verify      |
          +-----------v-------+------------------------+
          |                                            |
          |         RECONCILIATION ENGINE              |
          |                                            |
          |  +--------------------------------------+  |
          |  | TIER 1: Deterministic SQL Engine     |  |
          |  | src/db_reconciliation.py             |  |
          |  | Exact: ref + amount + customer + date|  |
          |  | Result: 389 RECONCILED, 111 escalated|  |
          |  +--------------------------------------+  |
          |                    |                       |
          |  +--------------------------------------+  |
          |  | TIER 2: Calibrated Signal Scoring    |  |
          |  | 0.93 threshold on validation split   |  |
          |  | Result: all 111 pass to Tier 3       |  |
          |  +--------------------------------------+  |
          |                    |                       |
          |  +--------------------------------------+  |
          |  | TIER 3: Gemini AI Investigator       |  |
          |  | ai/gemini_investigator.py            |  |
          |  | Native JSON + Pydantic + Policy Gate |  |
          |  | Result: 18 MATCH, 28 REVIEW, 65 UNRE |  |
          |  +--------------------------------------+  |
          |                                            |
          +--------------------------------------------+
```

---

## Data Flow Diagrams

### DFD Level 0 — Context Diagram

```
+-----------+                                              +-----------+
|  Merchant | ------ invoices.csv ------+                  |  Razorpay |
|  (ERP)    |                           |                  |  (API)    |
+-----------+                           v                  +-----------+
                              +-------------------+             |
                              |                   | <-- payments, settlements,
                              |    RECONPILOT     |     webhooks, combined recon
                              |   (AI Finance     |
                              |    Controller)    |             |
                              |                   | ---------> |
                              +-------------------+        +-----------+
                                /       |       \          |  Bank     |
                               /        |        \         | (Statement|
                    +---------+  +------+------+  +-----+  +-----------+
                    |Reconciled|  |  Exception  |  |Audit|
                    |  Cases   |  |   Queue     |  |Trail|
                    |  (389)   |  |   (111)     |  |(1100)|
                    +----------+  +-------------+  +-----+
```

### DFD Level 1 — Process Decomposition

```
+------------------------------------------------------------------------+
|                                                                        |
|  1.0 INGEST & NORMALIZE                                               |
|  [invoices, payments, settlements, bank] -> financial_records (1,190)  |
|                                                                        |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                                                                        |
|  2.0 DETERMINISTIC MATCHING (Tier 1)                                  |
|  For each invoice: find payment with matching ref + amount + date      |
|  Input:  500 invoice cases                                             |
|  Output: 389 RECONCILED | 111 ESCALATED                              |
|                                                                        |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                                                                        |
|  3.0 AI INVESTIGATION (Tier 2 + 3)                                    |
|  Build evidence packet per case -> Gemini API -> Pydantic validate     |
|  -> Policy gate (0.93) -> Route to MATCH / REVIEW / UNRESOLVED        |
|  Input:  111 ambiguous cases                                           |
|  Output: 73 REVIEW | 38 UNRESOLVED                                    |
|                                                                        |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                                                                        |
|  4.0 SETTLEMENT RECONCILIATION                                        |
|  Match payments to settlement lines (fee + tax deducted)              |
|  Match settlements to bank credits (UTR reference)                     |
|  Input:  531 payments, 543 settlement lines, 81 bank entries           |
|  Output: 531 payment-settlement links, bank verification               |
|                                                                        |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                                                                        |
|  5.0 HUMAN REVIEW & AUDIT                                             |
|  73 cases queued for analyst -> Approve/Reject/Override                |
|  Every action writes to audit_events (immutable)                       |
|  Output: Reconciled or exception with full audit trail                 |
|                                                                        |
+------------------------------------------------------------------------+
```

### DFD Level 2 — AI Investigation Detail

```
+------------+    +-----------------+    +------------------+
| 3.1 BUILD  |    | 3.2 CALL        |    | 3.3 VALIDATE     |
| EVIDENCE   |--->| GEMINI API      |--->| PYDANTIC         |
| PACKET     |    |                 |    | extra='forbid'    |
|            |    | Native JSON     |    | model_validator   |
| invoice +  |    | responseSchema  |    | decision_consist  |
| candidates |    | temperature=0.1 |    |                  |
+------------+    +-----------------+    +--------+---------+
                                                  |
                                         +--------v---------+
                                         | 3.4 POLICY GATE  |
                                         | - confidence >=  |
                                         |   0.93 to match  |
                                         | - payment_id in  |
                                         |   evidence packet |
                                         | - ownership check |
                                         +--------+---------+
                                                  |
                                    +-------------+-------------+
                                    |             |             |
                              +-----v---+  +-----v---+  +------v------+
                              | MATCH   |  | REVIEW  |  | UNRESOLVED  |
                              | (auto)  |  | (human) |  | (exception) |
                              +---------+  +---------+  +-------------+
```

---

## Three-Tier AI Engine

### Why Not Just Use AI for Everything?

> Track 04 evaluation parameter: **"AI Judgment — don't force AI where deterministic is better"**

| Decision | Reasoning |
|---|---|
| Tier 1 handles 77.8% deterministically | Exact ref + amount + date match needs no LLM — faster, cheaper, 100% precise |
| Tier 2 gates before AI | Calibrated threshold prevents wasting AI calls on trivially unsolvable cases |
| Tier 3 uses Gemini only for 111 ambiguous cases | Language reasoning on customer names, partial refs, date windows |
| Total AI cost for 500 invoices | **< $0.02** (111 calls x ~$0.000165/call) |

### Gemini Integration — Real Code

```python
# ai/gemini_investigator.py — Gemini v1beta with native JSON schema

SCHEMA = {
    "type": "object",
    "properties": {
        "decision":            {"enum": ["MATCH", "REVIEW", "UNRESOLVED"]},
        "selected_payment_id": {"type": "string", "nullable": True},
        "confidence":          {"minimum": 0, "maximum": 1},
        "evidence":            {"maxItems": 8},
        "risks":               {"maxItems": 8}
    },
    "required": ["decision", "selected_payment_id", "confidence", "evidence", "risks"]
}

# Rate guard: 14.28 RPM (4.2s between calls) — under 15 RPM free tier
# Fallback chain: gemini-2.5-flash-lite -> gemini-2.0-flash -> gemini-1.5-flash
# On 429: exponential backoff with Retry-After header
```

```python
# ai/decision_models.py — Pydantic v2 strict validation (second gate)

class ReconciliationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")   # rejects hallucinated fields
    decision: Literal["MATCH", "REVIEW", "UNRESOLVED"]
    selected_payment_id: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(max_length=8)
    risks: list[str] = Field(max_length=8)

    @model_validator(mode="after")
    def decision_consistency(self):
        # MATCH without payment_id -> reject
        # Non-MATCH with payment_id -> reject
```

```python
# Policy gate — runs AFTER Pydantic (third gate)
def validate_business_policy(decision, allowed_payment_ids):
    if decision.decision == "MATCH":
        if decision.selected_payment_id not in allowed_payment_ids:
            raise ReconciliationPolicyError(
                "Model selected a payment outside the evidence packet."
            )
```

---

## Razorpay Integration

### APIs Used

| Razorpay API | Endpoint | Usage |
|---|---|---|
| Payments | `GET /v1/payments` | Paginated fetch (100/page) of all captured payments |
| Settlements | `GET /v1/settlements` | Paginated fetch of settlement headers |
| Combined Recon | `GET /v1/settlements/recon/combined` | Per-payment settlement breakdown (up to 1000/req) |
| Webhooks | `POST /api/v1/webhooks/razorpay` | Real-time event ingestion |

### Webhook Security

```python
# api/webhooks.py — HMAC-SHA256 raw body verification

signature = hmac.new(
    webhook_secret.encode(),
    request.body,                  # raw bytes, not parsed JSON
    hashlib.sha256
).hexdigest()

# X-Razorpay-Event-Id -> idempotency key in webhook_events table
# Duplicate events rejected at DB level (PRIMARY KEY constraint)
```

### Events Handled

| Webhook Event | Action |
|---|---|
| `payment.captured` | Upsert payment record, trigger invoice match |
| `payment.failed` | Log to audit trail, flag linked invoice |
| `settlement.processed` | Upsert settlement, trigger settlement recon |
| `refund.processed` | Flag invoice for review |

### Fail-Closed Design

```
Missing GEMINI_API_KEY  -> GeminiInvestigatorError (500, no silent fallback)
Missing Razorpay keys   -> sync script logs warning, exits cleanly
Invalid webhook HMAC    -> 401, event not processed
Duplicate webhook       -> 200, event deduplicated via event_id
```

---

## AI Governance — Triple Gate

> Track 04 bar: *"Every money action explainable, bounded and gated. Show the audit trail."*

```
Gemini Response
      |
      v
+------------------+     +------------------+     +------------------+
| GATE 1           |     | GATE 2           |     | GATE 3           |
| Gemini Native    | --> | Pydantic v2      | --> | Business Policy  |
| JSON Schema      |     | extra='forbid'   |     | Gate             |
|                  |     | model_validator  |     |                  |
| Enforces field   |     | Rejects halluc.  |     | Checks payment   |
| types + enum     |     | fields + invalid |     | ownership in     |
| constraints      |     | MATCH/null combo |     | evidence packet  |
+------------------+     +------------------+     | Threshold >= 0.93|
                                                  +------------------+
                                                         |
                                                         v
                                                  +------------------+
                                                  | AUDIT EVENT      |
                                                  | Written to DB    |
                                                  | actor, model,    |
                                                  | confidence, case |
                                                  +------------------+
```

| Control | Implementation |
|---|---|
| Webhook authenticity | HMAC-SHA256 on raw body bytes |
| Duplicate webhooks | `X-Razorpay-Event-Id` as idempotency key |
| AI hallucination | Pydantic `extra='forbid'` + model_validator |
| Evidence ownership | Policy gate: payment_id must be in evidence packet |
| Auto-match threshold | 0.93 calibrated on validation split (never on test) |
| Ground truth isolation | `data/ground_truth_private.csv` never seen by model or UI |
| Audit trail | Every action logged: actor, timestamp, model, confidence |
| Secrets | `.env` pattern, `.gitignore` enforced |

---

## Benchmark and Accuracy

> PS-4 bar: *"Throughput plus measured accuracy plus an honest exception list."*

### Train / Validation / Test Split

| Split | Cases | Purpose |
|---|---|---|
| Train | 309 | Deterministic rule development |
| Validation | 103 | Threshold calibration (chose 0.93) |
| Test (held-out) | 88 | Final metrics — NEVER used for tuning |

### Held-Out Test Results (88 cases)

| Metric | Value |
|---|---|
| **Precision** | **96.61%** |
| **Recall** | **75.00%** |
| **F1 Score** | **84.44%** |
| True Positives | 57 |
| False Positives | 2 |
| False Negatives | 19 |

### Three-Tier Cost Matrix

| Tier | Engine | Cases | Precision | Cost | Latency |
|---|---|---|---|---|---|
| **1** | SQL Deterministic | 389 | **100.0%** | $0.00 | <10ms |
| **2** | Calibrated Gate | 88 test | **96.61%** | $0.00 | <50ms |
| **3** | Gemini AI | 111 exceptions | Gated 0.93 | ~$0.02 total | ~1.2s/case |

### Validation Split (103 cases — calibration only)

| Metric | Value |
|---|---|
| Precision | 97.62% |
| Recall | 84.54% |
| F1 | 90.61% |

---

## Exception List

> PS-4 bar: *"An honest exception list. One cherry-picked match proves nothing."*

**111 exceptions** are in the live queue at `/api/v1/exceptions/merchant_demo`.

Each exception record contains:
- `exception_id` — unique identifier
- `case_id` — links to reconciliation case
- `severity` — HIGH / MEDIUM / LOW
- `reason` — why it was flagged (e.g., "No matching payment found", "Amount mismatch", "Reference ambiguous")
- `status` — OPEN / ASSIGNED / RESOLVED
- `created_at` — timestamp

**Exception breakdown:**
- 38 invoices with **no payment found** at all (truly unresolved)
- 73 invoices with **ambiguous matches** routed to human review queue
- All 111 are visible in the UI Exception Queue tab

**These are NOT silently closed.** Every exception persists until a human analyst reviews and resolves it via the `/api/v1/cases/{case_id}/resolve` endpoint.

---

## What Broke at 2 AM

> Razorpay evaluation parameter: **"Failure Recovery — what broke at 2 AM and how you diagnosed and resolved it"**

### Bug 1: The Silent Zero (Exception Queue ReferenceError)

**What broke:** The Exception Queue tab showed **0 exceptions** instead of 111. No error visible in the UI.

**Root cause:** Variable scoping bug in `web/app.js`. The fetch callback used `rows` without declaring it:
```javascript
// BROKEN
fetch(`/api/v1/exceptions/${MID}`).then(r => r.json()).then(d => {
    // rows was never declared — ReferenceError
    rows.forEach(...)
});
```

**The fix:**
```javascript
// FIXED
fetch(`/api/v1/exceptions/${MID}`).then(r => r.json()).then(d => {
    let rows = d.items || [];  // explicit declaration
    rows.forEach(...)
});
```

**Why this matters:** This is EXACTLY the class of bug ReconPilot is built to prevent — **silent zeros in financial data**. An exception count showing 0 when it should show 111 is the digital equivalent of a finance team thinking "everything matched" when it didn't.

### Bug 2: The Inflated Exception Count (642 vs 111)

**What broke:** After running all three reconciliation stages, the exception count jumped to **642** instead of the expected 111.

**Root cause:** The payment-to-settlement reconciliation stage was running before settlements were fully populated in the database, generating 531 spurious "no matching settlement" exceptions.

**The fix:** Enforce stage ordering in the batch reconciliation script:
```python
# 1. Import all sources first (invoices, payments, settlements, bank)
# 2. Run invoice-to-payment matching (produces 111 real exceptions)
# 3. THEN run payment-to-settlement (requires settlements to exist)
# 4. THEN run settlement-to-bank (requires both above)
```

**Diagnosis method:** Queried exceptions by case_type:
```sql
SELECT case_type, COUNT(*) FROM exceptions e
JOIN reconciliation_cases c ON c.case_id = e.case_id
GROUP BY case_type;
-- invoice_to_payment: 111 (correct)
-- payment_to_settlement: 531 (spurious — ran before data existed)
```

### Bug 3: Gemini 429 Rate Limit Cascade

**What broke:** Batch AI investigation of 111 cases crashed after ~15 calls with `429 Too Many Requests`.

**Root cause:** Free Gemini tier allows 15 RPM. Our initial implementation had no pacing.

**The fix:** Built a rate guard with 4.2-second inter-call delay (14.28 RPM, safely under 15 RPM limit):
```python
# 3-attempt retry with Retry-After header respect
for attempt in range(3):
    r = requests.post(url, json=body, timeout=45)
    if r.status_code == 429:
        wait_sec = int(r.headers.get("Retry-After", 5 * (attempt + 1)))
        time.sleep(wait_sec)
        continue
```

Added model fallback chain: `gemini-2.5-flash-lite -> gemini-2.0-flash -> gemini-1.5-flash`

---

## Database Schema

```sql
-- 7 tables with FK enforcement (PRAGMA foreign_keys = ON)

financial_records       -- 1,655 normalized records across 4 sources
reconciliation_cases    -- 1,031 cases: status + confidence + decision_source
reconciliation_links    -- evidence links: from_record -> to_record
exceptions              -- 111 flagged cases awaiting resolution
audit_events            -- 1,100+ immutable log entries (AI + human)
webhook_events          -- 4 HMAC-verified Razorpay webhook payloads
merchants               -- merchant registry
```

**Indexes:**
- `idx_financial_records_source` (merchant_id, source, record_type)
- `idx_cases_status` (merchant_id, status)
- `idx_audit_case` (case_id)

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health check |
| `/api/v1/overview/{merchant_id}` | GET | Live DB counts (records, cases, exceptions) |
| `/api/v1/cases/{merchant_id}` | GET | List cases, filterable by status |
| `/api/v1/cases/detail/{case_id}` | GET | Full case detail + links + exceptions + review candidates |
| `/api/v1/cases/{case_id}/resolve` | POST | Human review: APPROVE / REJECT / OVERRIDE |
| `/api/v1/exceptions/{merchant_id}` | GET | Exception queue with severity, reason, AI metadata |
| `/api/v1/benchmark` | GET | Live benchmark metrics + architecture matrix |
| `/api/v1/chain/{identifier}` | GET | Full Invoice -> Payment -> Settlement -> Bank chain |
| `/api/v1/ai/investigate/{case_id}` | POST | Trigger live Gemini investigation |
| `/api/v1/ai/status` | GET | AI key status, model, rate guard info |
| `/api/v1/import/upload` | POST | Upload single CSV document |
| `/api/v1/import/batch-upload` | POST | Upload multiple CSVs + optional auto-reconcile |
| `/api/v1/db/delete-documents` | POST | Delete records by source type |
| `/api/v1/import/demo` | POST | Reset to benchmark data (1,190 records) |
| `/api/v1/reconcile/run` | POST | Trigger full reconciliation pass |
| `/api/v1/demo/stream` | GET | SSE stream: 9-step reconciliation animation |
| `/api/v1/dashboard/{merchant_id}` | GET | Dashboard data + recent audit events |

---

## Project Structure

```
reconpilot_phase14_final/
|
+-- api/
|   +-- app.py              <- FastAPI: 17 REST + SSE endpoints
|   +-- models.py           <- Pydantic request/response models
|   +-- webhooks.py         <- Razorpay webhook HMAC handler
|
+-- ai/
|   +-- gemini_investigator.py  <- Gemini API caller + rate guard + fallback
|   +-- investigator.py         <- Router: Gemini vs offline
|   +-- decision_models.py      <- ReconciliationDecision (Pydantic v2)
|   +-- openai_investigator.py  <- OpenAI fallback
|
+-- db/
|   +-- database.py         <- SQLite init + connection
|   +-- repository.py       <- DB reads/writes (cases, exceptions, audit)
|   +-- schema.sql          <- 7-table schema, FK constraints, indexes
|   +-- reconpilot.db       <- Live database (5MB)
|
+-- src/
|   +-- db_reconciliation.py <- Tier 1 deterministic engine
|   +-- common.py            <- Shared utilities
|
+-- integrations/
|   +-- razorpay_client.py  <- Razorpay REST adapter
|
+-- scripts/
|   +-- import_benchmark.py             <- Load benchmark CSVs
|   +-- run_ai_controller.py            <- Batch Gemini runner
|   +-- reconcile_payment_settlement.py <- Stage 2 recon
|   +-- reconcile_settlement_bank.py    <- Stage 3 recon
|   +-- sync_razorpay_test.py           <- Live Test Mode sync
|
+-- data/
|   +-- invoices.csv             <- 500 invoices
|   +-- payments.csv             <- 531 payments
|   +-- settlements.csv          <- 76 settlement headers
|   +-- settlement_lines.csv     <- 543 settlement lines
|   +-- bank_statement.csv       <- 81 bank entries
|   +-- ground_truth_private.csv <- EVALUATION ONLY (never seen by AI)
|
+-- web/
|   +-- index.html          <- Control Room UI
|   +-- app.js              <- Frontend logic (fetch, SSE, DOM binding)
|
+-- tests/                  <- pytest suite (10/10 passing)
+-- requirements.txt
+-- .env.example
```

---

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
USE_LIVE_LLM=true
LLM_PROVIDER=gemini

# Optional (Razorpay Test Mode)
RAZORPAY_KEY_ID=rzp_test_xxxx
RAZORPAY_KEY_SECRET=xxxx
RAZORPAY_WEBHOOK_SECRET=xxxx
```

---

## Verification Checklist

```bash
# Tests
pytest -q                              # 10 passed

# Server
curl http://127.0.0.1:8000/health      # {"status":"ok"}

# DB counts
curl http://127.0.0.1:8000/api/v1/overview/merchant_demo
# financial_records: 1655, reconciliation_cases: 1031, exceptions: 111

# Benchmark
curl http://127.0.0.1:8000/api/v1/benchmark
# precision: 0.9661, recall: 0.75, f1: 0.8444

# AI key
curl http://127.0.0.1:8000/api/v1/ai/status
# has_key: true

# Compile check
python -m py_compile api/app.py ai/gemini_investigator.py ai/decision_models.py
```

---

## Judging Matrix

> How ReconPilot maps to Razorpay's 4 evaluation parameters:

### 1. Problem Taste

| Criterion | Evidence |
|---|---|
| Real-world finance problem | Month-end reconciliation across 4 financial sources |
| Meaningful scale | 500 invoices (10x the 50-record minimum) |
| Not a toy demo | Full invoice->payment->settlement->bank chain |
| Why it matters | 4-8 hours manual effort -> <2 minutes automated |

### 2. Build Quality

| Criterion | Evidence |
|---|---|
| Clean repo | Modular: api/ + ai/ + db/ + src/ + integrations/ + scripts/ |
| Tests passing | `pytest -q` -> 10 passed |
| Production patterns | FK constraints, HMAC webhooks, idempotency, audit trail |
| Not spaghetti | 7-table normalized schema, Pydantic v2 contracts, typed Python |

### 3. AI Judgment

| Criterion | Evidence |
|---|---|
| Don't force AI | Tier 1 handles 77.8% deterministically (zero AI) |
| AI where it adds value | Only 111/500 (22.2%) need Gemini — the genuinely ambiguous cases |
| Guardrails | Triple gate: Gemini Schema + Pydantic + Policy Gate |
| Honest metrics | Held-out test split, not contaminated, precision 96.61% |

### 4. Failure Recovery ("What Broke at 2 AM")

| Bug | Impact | Root Cause | Fix |
|---|---|---|---|
| Silent zero exceptions | UI showed 0 instead of 111 | JS variable scope (`rows` undeclared) | Explicit `let rows = d.items \|\| []` |
| Inflated exception count | 642 instead of 111 | Stage ordering — settlement recon ran before data loaded | Enforced sequential stage execution |
| Gemini 429 cascade | Batch AI crashed after 15 calls | No rate guard on free tier (15 RPM) | 4.2s delay + Retry-After backoff + model fallback |

---

*ReconPilot — Built for Razorpay AI Buildathon 2026 | Track 04 | Problem Statement 4*

*"Throughput plus measured accuracy plus an honest exception list. One cherry-picked match proves nothing."*
