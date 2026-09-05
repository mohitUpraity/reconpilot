# ReconPilot — 5-Minute Video Demo Script

> **For:** Razorpay AI Buildathon 2026 — Track 04 — AI Finance Controller
> **Total runtime:** 5:00 (300 seconds)
> **Tone:** Confident, technical, story-driven. No filler.
> **Key difference:** We start from EMPTY DB, ingest documents live, then reconcile.

---

## Timeline Overview

| Time | Scene | Duration |
|---|---|---|
| 0:00 - 0:20 | Hook: The Pain | 20s |
| 0:20 - 0:45 | Show Empty Dashboard (Zero State) | 25s |
| 0:45 - 1:30 | Delete Old Data + Batch Upload Documents | 45s |
| 1:30 - 2:15 | Run Reconciliation (SSE Stream) | 45s |
| 2:15 - 2:45 | Show Results — Dashboard Comes Alive | 30s |
| 2:45 - 3:30 | Exception Queue + Live Gemini Investigation | 45s |
| 3:30 - 3:55 | Finance Chain (Invoice -> Bank Trace) | 25s |
| 3:55 - 4:20 | Human Review + Audit Trail | 25s |
| 4:20 - 4:40 | Benchmark + AI Judgment | 20s |
| 4:40 - 4:55 | What Broke at 2 AM | 15s |
| 4:55 - 5:00 | Closing | 5s |

---

## Pre-Recording Checklist

```bash
# 1. Server running
uvicorn api.app:app --reload --port 8000

# 2. IMPORTANT: Delete all documents before recording so DB is empty
#    Do this from the UI "Update DB" button, or:
curl -X POST http://127.0.0.1:8000/api/v1/db/delete-documents \
  -H "Content-Type: application/json" \
  -d '{"source_types": ["invoice", "payment", "settlement", "bank"]}'

# 3. Verify DB is empty
curl http://127.0.0.1:8000/api/v1/overview/merchant_demo
# expect: financial_records=0, reconciliation_cases=0, exceptions=0

# 4. AI key working
curl http://127.0.0.1:8000/api/v1/ai/status
# expect: has_key=true

# 5. Tests pass
pytest -q
# expect: 10 passed

# 6. Keep these CSV files ready to upload:
#    data/invoices.csv (500 rows)
#    data/payments.csv (531 rows)
#    data/settlements.csv (76 rows)
#    data/settlement_lines.csv (543 rows)
#    data/bank_statement.csv (81 rows)

# 7. Browser open to http://127.0.0.1:8000 — Control Room tab active
```

---

## Scene 1 — Hook: The Pain (0:00 - 0:20)

### Show on screen:
- Your face / screen recording intro
- Then switch to the browser showing ReconPilot Control Room

### Say:
> "It's month-end. Finance team has five hundred invoices, Razorpay payment data,
> settlement reports, and a bank statement. They need to match everything.
> Today that takes six hours, two analysts, and still has errors.
> ReconPilot does it in under two minutes. Let me show you — from scratch."

---

## Scene 2 — Show Empty Dashboard (0:20 - 0:45)

### Show on screen:
- Control Room dashboard showing **all zeros**
- Point at the KPI bar: 0 records, 0 cases, 0 exceptions
- The dashboard is empty — no data loaded

### Say:
> "Right now the database is completely empty. Zero records. Zero cases. Zero exceptions.
> No data has been loaded. This is a clean slate.
> I'm going to ingest real financial documents, run the reconciliation engine,
> and show you every result — live."

---

## Scene 3 — Delete Old Data + Batch Upload Documents (0:45 - 1:30)

### Show on screen:
- Click the **"Update DB"** button in the UI
- Show the delete modal — click "Delete All" to clear any remaining data
- Then click **"Upload Documents"** or use the batch upload feature
- Select ALL 4 CSV files: invoices.csv, payments.csv, settlements.csv + settlement_lines.csv, bank_statement.csv
- Show the upload progress
- After upload completes, dashboard numbers update live

### Say:
> "First, let me clear any existing data. Delete all — invoices, payments, settlements, bank.
> Database is clean.
> Now I'll upload the financial documents. These are four CSV files —
> five hundred invoices from the merchant's ERP,
> five hundred thirty-one payments from Razorpay,
> seventy-six settlement headers with five hundred forty-three per-payment settlement lines,
> and eighty-one bank statement entries.
> [PAUSE while upload completes]
> Upload complete. Watch the dashboard — the numbers just appeared.
> One thousand six hundred fifty-five financial records ingested and normalized.
> But nothing is reconciled yet. Let me run the engine."

---

## Scene 4 — Run Reconciliation (SSE Stream) (1:30 - 2:15)

### Show on screen:
- Click **"Run Demo"** button on Control Room
- Watch the SSE streaming animation — 9 steps flowing live
- Each step appears in real time

### Say:
> "Watch the reconciliation cycle run live.
> Step one: four financial sources detected — invoices, payments, settlements, bank.
> Step two: one thousand one hundred ninety records normalized into a unified schema.
> Step three: five hundred invoice cases scanned.
> Step four: the deterministic engine fires — it matches by reference, amount, customer, and date.
> Three hundred eighty-nine invoices reconciled instantly. Zero AI cost. Under ten milliseconds.
> Step five: one hundred eleven ambiguous cases — where references don't match cleanly —
> routed to the AI investigator.
> Step six: Gemini processes each one with structured JSON output.
> Step seven: the policy gate runs — blocks anything under zero-point-nine-three confidence.
> Step eight: seventy-three cases queued for human review.
> Step nine: cycle complete. Let me show you the results."

---

## Scene 5 — Dashboard Comes Alive (2:15 - 2:45)

### Show on screen:
- Scroll through the Control Room — all numbers are now populated
- Point at the status cards: RECONCILED 389, REVIEW 73, UNRESOLVED 38
- Point at the pipeline visualization

### Say:
> "Two minutes ago this dashboard was empty. Now look at it.
> Three hundred eighty-nine invoices auto-reconciled — tier one, deterministic, no AI.
> Seventy-three in human review — the AI found matches but confidence wasn't high enough for auto-approval.
> Thirty-eight truly unresolved — no payment exists for these invoices.
> One hundred eleven exceptions — every ambiguous case is here, none silently closed.
> Every number is a live database query. Refresh the page — it stays the same."

---

## Scene 6 — Exception Queue + Live Gemini Investigation (2:45 - 3:30)

### Show on screen:
- Click **Exception Queue** tab
- Show the 111 exceptions with severity, case type, confidence, reason
- Click one exception to open the Case Detail drawer
- Click **"Investigate with Gemini"** button
- WAIT for the live response (let the 1-2 second latency show — proves it's real)

### Say:
> "The problem statement asks for an honest exception list. Here are all one hundred eleven.
> Each one has severity, reason, and the case type.
> Let me click one. This invoice had an amount match but the reference didn't align.
> I'll trigger a live Gemini investigation.
> [PAUSE — let it load]
> The AI returns structured JSON: decision, confidence, evidence bullets, risk factors.
> But before this touches the database, it passes through three gates.
> Gate one: Gemini's native JSON schema — enforces field types and enums.
> Gate two: Pydantic with extra-equals-forbid — any hallucinated field gets rejected.
> Gate three: the business policy gate — checks that the selected payment ID
> actually exists in the evidence packet. Not just valid JSON — valid finance logic.
> Three layers of governance before a single write."

---

## Scene 7 — Finance Chain (3:30 - 3:55)

### Show on screen:
- Navigate to **Finance Chain** tab
- Show the four-node chain: Invoice -> Payment -> Settlement -> Bank
- Highlight the fee deduction math

### Say:
> "The hardest reconciliation problem: the settlement amount never equals the invoice.
> Razorpay deducts fees and GST before crediting the bank.
> Finance Chain shows the full money trail:
> Invoice forty-two thousand eight hundred. Payment captured at full amount.
> Settlement: fee deducted, GST deducted, net forty-two thousand four hundred nineteen.
> Bank credited with UTR reference. End-to-end — one API call."

---

## Scene 8 — Human Review + Audit Trail (3:55 - 4:20)

### Show on screen:
- Click **Human Review** tab — show 73 cases
- Click one case, show the Approve / Reject / Override buttons
- Click **Audit Trail** tab — show the immutable log

### Say:
> "Seventy-three cases need a human. Analyst sees the AI recommendation, evidence, and risks.
> They can approve, reject, or override with a note.
> Every action writes an immutable audit event — who acted, which AI model,
> what confidence triggered the routing.
> This is governance. Not just a queue — a full audit trail for regulators."

---

## Scene 9 — Benchmark + AI Judgment (4:20 - 4:40)

### Show on screen:
- Click **Benchmark & Policy** tab
- Point at precision 96.61%, F1 84.44%

### Say:
> "On the held-out test split — eighty-eight cases the model never saw during calibration —
> precision ninety-six-point-six percent. F1 eighty-four-point-four.
> The threshold was calibrated on a separate validation split. Test data was never used for tuning.
> AI Judgment: tier one handles seventy-seven percent of cases deterministically at zero cost.
> We don't force AI where rules work better. Total Gemini cost for all exceptions: under two cents."

---

## Scene 10 — What Broke at 2 AM (4:40 - 4:55)

### Show on screen:
- Split screen showing code or just speak to camera

### Say:
> "What broke? Three things.
> The exception queue showed zero instead of one-eleven — a silent JavaScript scope bug.
> The exception count inflated to six hundred forty-two — stage ordering, settlement recon ran
> before data loaded.
> And Gemini rate-limited at fifteen RPM on free tier — fixed with a four-point-two second pacer
> and a model fallback chain.
> Every one of these is a real failure we diagnosed and fixed."

---

## Scene 11 — Closing (4:55 - 5:00)

### Show on screen:
- Terminal: `pytest -q` -> 10 passed
- Return to Control Room

### Say:
> "ReconPilot. From empty database to fully reconciled — in under two minutes.
> Five hundred invoices. One hundred eleven exceptions. Honestly reported.
> Track Four. AI Finance Controller. Thank you."

---

## Key Moments That Win Points

| Moment | Why It Matters |
|---|---|
| Empty dashboard -> populated dashboard | Proves data isn't hardcoded, shows the full lifecycle |
| Batch upload of 4 CSVs | Shows document ingestion capability |
| SSE stream with 9 steps | Proves real-time processing, not a static page |
| Gemini investigation with visible latency | Proves live AI, not cached |
| "Pydantic extra equals forbid" | Hallucination guard — judges love this |
| "Held-out test split, never used for tuning" | Evaluation integrity |
| "AI only for 22% of cases" | AI Judgment parameter |
| "Honest exception list" | Directly quotes PS-4 bar |

---

## What NOT to Do

1. **Don't start with data already loaded** — the empty-to-full transition IS the demo
2. **Don't say "in production it would"** — this IS production-grade
3. **Don't rush the Gemini investigation** — let the latency prove it's real
4. **Don't skip the exception count** — 111 is the star number
5. **Don't forget "held-out test split"** — judges dock for benchmark contamination
6. **Don't read from a script** — know your numbers cold

---

## If You Need to Trim (Cut Order)

Cut these first (lowest impact):
1. Finance Chain (Scene 7) — just mention "we have an endpoint for it"
2. Human Review detail (Scene 8) — show the queue, skip the resolve action
3. Benchmark (Scene 9) — reduce to 10 seconds, two numbers only

**NEVER cut:**
- Empty dashboard -> upload -> reconcile flow (this IS the demo)
- Exception queue + Gemini investigation (core PS-4 requirement)
- "What broke" (mandatory evaluation parameter)
- The closing "honest exception list" line
