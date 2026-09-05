# ReconPilot — 5-Minute Video Demo Script

> **For:** Razorpay AI Buildathon 2026 — Track 04 — AI Finance Controller
> **Total runtime:** 5:00 (300 seconds)
> **Tone:** Confident, punchy, story-driven. No filler. No "um". No "basically".
> **Key difference:** We start from EMPTY DB → ingest live → reconcile live → everything is real.
> **Fix My Itch reference:** ITCH Score 67.5 — "Why do micro-SMEs waste 10+ hours weekly on invoice management?"

---

## Judging Parameters — Where Each Scene Scores

| Parameter | Scenes That Prove It |
|---|---|
| 🎯 **Problem Taste** | Scene 1 (Fix My Itch), Scene 3 (real data), Scene 5 (results) |
| 🔧 **Build Quality** | Scene 3 (ingestion), Scene 4 (SSE pipeline), Scene 8 (audit), Scene 11 (tests) |
| 🧠 **AI Judgment** | Scene 4 (tier split), Scene 6 (triple gate), Scene 9 (benchmark) |
| 💥 **Failure Recovery** | Scene 10 (3 real bugs with root cause + fix) |

---

## Timeline Overview

| Time | Scene | Duration | Proves |
|---|---|---|---|
| 0:00 – 0:25 | 🔥 Hook: The Itch | 25s | Problem Taste |
| 0:25 – 0:45 | Empty Dashboard | 20s | Build Quality |
| 0:45 – 1:30 | Delete + Batch Upload | 45s | Problem Taste + Build Quality |
| 1:30 – 2:15 | Run Reconciliation (SSE) | 45s | AI Judgment + Build Quality |
| 2:15 – 2:45 | Dashboard Comes Alive | 30s | Problem Taste |
| 2:45 – 3:30 | Exception Queue + Gemini | 45s | AI Judgment |
| 3:30 – 3:55 | Finance Chain | 25s | Problem Taste |
| 3:55 – 4:20 | Human Review + Audit | 25s | Build Quality |
| 4:20 – 4:40 | Benchmark + AI Judgment | 20s | AI Judgment |
| 4:40 – 4:55 | What Broke at 2 AM | 15s | Failure Recovery |
| 4:55 – 5:00 | Closing | 5s | — |

---

## Pre-Recording Checklist

```bash
# 1. Server running
uvicorn api.app:app --reload --port 8000

# 2. IMPORTANT: Delete all documents so DB is empty
curl -X POST http://127.0.0.1:8000/api/v1/db/delete-documents \
  -H "Content-Type: application/json" \
  -d '{"source_types": ["invoice", "payment", "settlement", "bank"]}'

# 3. Verify DB is empty
curl http://127.0.0.1:8000/api/v1/overview/merchant_demo
# expect: financial_records=0, reconciliation_cases=0, exceptions=0

# 4. AI key working
curl http://127.0.0.1:8000/api/v1/ai/status
# expect: has_key=true

# 5. Tests pass (run unit tests only — integration test needs data)
.venv/bin/pytest tests/ -q
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

## Scene 1 — 🔥 Hook: The Itch (0:00 – 0:25)

> **PROVES: 🎯 Problem Taste** — real pain, real scale, real user

### Show on screen:
- **Flash** the Razorpay "Fix My Itch" leaderboard page (`razorpay.com/m/fix-my-itch`)
- Zoom into the problem card: *"Why do micro-SMEs waste 10+ hours weekly on invoice management?"*
- Highlight the ITCH Score: **67.5**
- Quick cut → your empty ReconPilot Control Room

### Say:
> "Sixty-seven point five.
> That's the ITCH score on Razorpay's own Fix My Itch leaderboard for this problem:
> *Why do micro-SMEs waste ten-plus hours every week just managing invoices?*
>
> Here's why it's broken.
> Invoice says forty-two thousand eight hundred. Bank says forty-two thousand four hundred nineteen.
> Razorpay ate three hundred eighty-one in fees and GST — silently.
> References don't match. Amounts don't match. Dates drift.
> Nobody knows which invoices got paid until the quarterly audit — by then, cash flow is a guess.
>
> I built the fix. It's called ReconPilot.
> And in the next four minutes, I'm going to take an empty database,
> ingest real financial documents, and reconcile five hundred invoices live.
> No hardcoded data. No cherry-picked matches. Let's go."

### 🎯 Why this intro works:
- Opens with a **number** (67.5) — grabs attention
- References Razorpay's **own platform** — shows you did homework
- Describes the **real pain** in one concrete example (42,800 vs 42,419)
- Promises a **live proof** — not slides, not screenshots
- "No cherry-picked matches" — **directly quotes PS-4's bar**

---

## Scene 2 — Empty Dashboard (0:25 – 0:45)

> **PROVES: 🔧 Build Quality** — the app works with zero data, no crashes

### Show on screen:
- Control Room showing **all zeros**
- Hover over each KPI card: 0 records, 0 cases, 0 exceptions
- Quickly scroll down — empty tables, empty charts

### Say:
> "Right now — zero. Zero records. Zero cases. Zero exceptions.
> The database is completely empty. Nothing preloaded, nothing cached.
> I'm going to populate this entire dashboard from raw CSV files — live."

---

## Scene 3 — Delete + Batch Upload Documents (0:45 – 1:30)

> **PROVES: 🎯 Problem Taste** (real data scale) + **🔧 Build Quality** (ingestion pipeline)

### Show on screen:
- Click **"Update DB"** button
- If any stale data exists → click "Delete All" → confirm
- Dashboard resets to zeros
- Click **"Upload Documents"** / batch upload
- Select ALL CSV files:
  - `invoices.csv` (500 rows)
  - `payments.csv` (531 rows)
  - `settlements.csv` (76 headers)
  - `settlement_lines.csv` (543 line items)
  - `bank_statement.csv` (81 entries)
- Show the upload progress indicator
- After upload → dashboard numbers update live

### Say:
> "First, clear everything. Delete all — invoices, payments, settlements, bank. Gone.
>
> Now, batch upload. These are four financial data sources —
> five hundred invoices from the merchant's ERP system,
> five hundred thirty-one payment captures from Razorpay's API,
> seventy-six settlement headers with five forty-three per-payment line items,
> and eighty-one bank statement entries from HDFC.
>
> [PAUSE — let upload complete]
>
> Done. One thousand six hundred fifty-five financial records ingested.
> Each one parsed, normalized, and stored with foreign-key integrity.
> But nothing is reconciled yet. These are just raw records. Watch what happens next."

### 💡 Tip:
- **Don't rush the upload.** Let the progress bar finish on screen — it proves real I/O, not a mock.
- If upload is fast, that's even better — shows performance.

---

## Scene 4 — Run Reconciliation (SSE Stream) (1:30 – 2:15)

> **PROVES: 🧠 AI Judgment** (tier split: deterministic vs AI) + **🔧 Build Quality** (real-time SSE)

### Show on screen:
- Click **"Run Demo"** on Control Room
- Watch the 9-step SSE stream animate live
- Each step appears in real time with progress updates

### Say:
> "Run reconciliation. Watch the pipeline — nine steps, streaming live via Server-Sent Events.
>
> Step one — four financial sources detected.
> Step two — one thousand one hundred ninety records normalized into a unified schema.
> Step three — five hundred invoice cases generated.
>
> **Now here's the AI Judgment call.**
>
> Step four — the deterministic matcher fires first. No AI. Pure rules:
> reference matching, amount matching, customer and date cross-validation.
> Three hundred eighty-nine invoices matched instantly. Under ten milliseconds. Zero API cost.
>
> Step five — one hundred eleven cases are genuinely ambiguous. References don't align.
> ONLY these go to AI.
>
> This is the split: seventy-seven-point-eight percent handled by rules.
> Twenty-two-point-two percent by Gemini.
> We don't force AI where deterministic logic works better.
>
> Step six through nine — Gemini processes each exception, policy gates fire,
> seventy-three cases routed to human review, cycle complete.
> Let me show you the results."

### 🧠 Key phrase to say clearly:
> "Seventy-seven percent deterministic, twenty-two percent AI. We don't force AI where rules work better."
> *(This is the exact thing judges score under "AI Judgment")*

---

## Scene 5 — Dashboard Comes Alive (2:15 – 2:45)

> **PROVES: 🎯 Problem Taste** — the transformation from zero to reconciled

### Show on screen:
- Scroll the Control Room — all KPIs now populated
- Point at status breakdown: **RECONCILED 389 | REVIEW 73 | UNRESOLVED 38**
- Point at the pipeline visualization
- Optionally: **refresh the page** to prove it's persisted in DB

### Say:
> "Two minutes ago this was all zeros. Look at it now.
>
> Three hundred eighty-nine invoices auto-reconciled — tier one, no AI.
> Seventy-three in human review — AI found matches but confidence was below the policy threshold.
> Thirty-eight truly unresolved — no matching payment exists for these invoices.
> And one hundred eleven total exceptions — every single ambiguous case is tracked. None silently closed.
>
> This isn't a rendered template. Let me refresh the page. Same numbers.
> Every count is a live database query against a seven-table normalized schema."

---

## Scene 6 — Exception Queue + Live Gemini Investigation (2:45 – 3:30)

> **PROVES: 🧠 AI Judgment** — triple validation gate, honest exception list

### Show on screen:
- Click **Exception Queue** tab
- Show all 111 exceptions with severity, type, confidence, reason
- Click ONE exception to open the Case Detail drawer
- Click **"Investigate with Gemini"** button
- **WAIT for the response** — let the 1-2 second latency show on screen (proves it's live)

### Say:
> "PS-4 says: *'an honest exception list — one cherry-picked match proves nothing.'*
> Here are all one hundred eleven. Every one. Severity, case type, reason, confidence.
>
> Let me click one. This invoice — amount matched but reference drifted. Classic Razorpay problem.
> I'll trigger a live Gemini investigation.
>
> [PAUSE — let it load. Don't talk. The latency IS the proof.]
>
> Structured JSON back: decision, confidence zero-point-nine-five, evidence bullets, risk factors.
> But — here's what matters — before this touches the database, it passes three gates:
>
> **Gate one:** Gemini's native response schema — enforces field types, enums, required fields at the API level.
> **Gate two:** Pydantic with `extra='forbid'` — any hallucinated field the model invents? Rejected.
> **Gate three:** Business policy gate — verifies the AI's chosen payment ID actually exists in the evidence packet.
> Not just valid JSON. Valid finance logic.
>
> Three layers of governance. This is how you trust an AI in finance."

### 🧠 Key phrases to say clearly:
- "Pydantic extra equals forbid" — judges love this
- "Three gates" — memorable structure
- "Not just valid JSON — valid finance logic" — the money line

---

## Scene 7 — Finance Chain (3:30 – 3:55)

> **PROVES: 🎯 Problem Taste** — you understand the real reconciliation problem (fee deductions)

### Show on screen:
- Navigate to **Finance Chain** tab
- Show the four-node chain: **Invoice → Payment → Settlement → Bank**
- Highlight the fee deduction math

### Say:
> "This is why reconciliation is actually hard.
> The bank never credits the invoice amount.
> Razorpay deducts platform fees and GST before settling.
>
> Finance Chain traces the full money trail:
> Invoice forty-two thousand eight hundred. Payment captured at full amount.
> Settlement: fee three-twelve, GST sixty-nine, net forty-two thousand four-nineteen.
> Bank credited with UTR reference. End-to-end — one API call, four financial entities connected.
>
> This is the chain that breaks every Excel reconciliation."

---

## Scene 8 — Human Review + Audit Trail (3:55 – 4:20)

> **PROVES: 🔧 Build Quality** — governance, not just a queue

### Show on screen:
- Click **Human Review** tab — show the 73 cases
- Click one case → show Approve / Reject / Override buttons
- Click **Audit Trail** tab → show the immutable event log

### Say:
> "Seventy-three cases need a human.
> The analyst sees the AI's recommendation, evidence, confidence, and risk factors.
> They can approve, reject, or override with a written note.
>
> Every action — every click — writes an immutable audit event.
> Who acted, when, which AI model, what confidence triggered the routing.
>
> This isn't a to-do list. This is an audit trail for finance regulators.
> SOX-ready. Every decision traceable."

---

## Scene 9 — Benchmark + AI Judgment (4:20 – 4:40)

> **PROVES: 🧠 AI Judgment** — measured accuracy, not a cherry-picked demo

### Show on screen:
- Click **Benchmark & Policy** tab
- Point at: **Precision 96.61%, F1 84.44%**
- Point at the threshold calibration note

### Say:
> "On the held-out test split — eighty-eight cases the model never saw during calibration —
> precision ninety-six-point-six percent. F1 eighty-four-point-four.
>
> The threshold was calibrated on a separate validation split.
> Test data was never used for tuning. No contamination.
>
> Total Gemini API cost for all one hundred eleven exceptions: under two cents.
> Because seventy-seven percent of cases never touched AI at all.
>
> PS-4 says: *'throughput plus measured accuracy plus an honest exception list.'*
> All three. Right here."

### 🧠 Key phrase:
> "Held-out test split — never used for tuning" — judges dock points for benchmark contamination

---

## Scene 10 — 💥 What Broke at 2 AM (4:40 – 4:55)

> **PROVES: 💥 Failure Recovery** — the mandatory evaluation parameter

### Show on screen:
- Speak directly to camera, or show a split-screen with relevant code

### Say:
> "What broke? Three things.
>
> **Bug one:** The exception queue showed zero instead of one-eleven.
> Root cause — a JavaScript scope bug. Variable `rows` was undeclared, silently fell back to empty.
> Fix: explicit `let rows = d.items || []`.
>
> **Bug two:** Exception count inflated to six hundred forty-two.
> Root cause — stage ordering. Settlement reconciliation ran before payment data finished loading.
> Fix: enforced sequential stage execution with dependency gates.
>
> **Bug three:** Gemini rate-limited at fifteen requests per minute on free tier.
> Entire batch AI pipeline crashed after the fifteenth call.
> Fix: four-point-two second pacer, Retry-After header backoff, and a model fallback chain —
> flash-lite as primary, pro as backup.
>
> Every one of these is a real failure I diagnosed, root-caused, and fixed.
> Not a hypothetical. Not a 'would have broken.' Did break. Did fix."

### 💥 Key phrase:
> "Did break. Did fix." — this is the line judges remember

---

## Scene 11 — Closing (4:55 – 5:00)

### Show on screen:
- Terminal: `pytest -q` → **10 passed**
- Return to Control Room — full dashboard visible

### Say:
> "ReconPilot. Empty database to fully reconciled — under two minutes.
> Five hundred invoices. One hundred eleven exceptions. Honestly reported.
> Every match audited. Every failure documented.
> Track Four. AI Finance Controller. Thank you."

---

## Scoring Cheat Sheet — What To Emphasize

> Reference this before recording. Each row = one thing judges will explicitly evaluate.

| Judging Parameter | What to Say | When to Say It |
|---|---|---|
| 🎯 **Problem Taste** | "ITCH score sixty-seven-point-five" | Scene 1, first 10 seconds |
| 🎯 **Problem Taste** | "Ten hours a week" / "Four to eight hours manual → under two minutes" | Scene 1 |
| 🎯 **Problem Taste** | "Five hundred invoices — ten times the fifty-record minimum" | Scene 3 |
| 🔧 **Build Quality** | "Seven-table normalized schema with foreign-key integrity" | Scene 5 |
| 🔧 **Build Quality** | "Server-Sent Events streaming live" | Scene 4 |
| 🔧 **Build Quality** | "Immutable audit trail — SOX-ready" | Scene 8 |
| 🔧 **Build Quality** | "pytest ten passed" | Scene 11 |
| 🧠 **AI Judgment** | "Seventy-seven percent deterministic, twenty-two percent AI" | Scene 4 |
| 🧠 **AI Judgment** | "Three gates: Gemini schema, Pydantic forbid, policy gate" | Scene 6 |
| 🧠 **AI Judgment** | "Held-out test split, never used for tuning" | Scene 9 |
| 🧠 **AI Judgment** | "Total cost: under two cents" | Scene 9 |
| 💥 **Failure Recovery** | "Did break. Did fix." | Scene 10 |
| 💥 **Failure Recovery** | Mention all 3 bugs with root cause | Scene 10 |

---

## Key Moments That Win Points

| Moment | Why It Matters |
|---|---|
| Opening with "67.5" | Starts with a number — grabs attention instantly |
| "Fix My Itch" reference | Shows you understand Razorpay's ecosystem, not just PS-4 |
| Empty dashboard → populated | Proves data isn't hardcoded, shows the full lifecycle |
| Batch upload of 5 CSVs | Shows document ingestion at scale |
| SSE stream with 9 steps | Proves real-time processing, not a static page |
| Gemini investigation with visible latency | Proves live AI, not cached results |
| "Pydantic extra equals forbid" | Hallucination guard — judges love this |
| "Three gates" | Memorable, repeatable structure |
| "Held-out test split, never used for tuning" | Evaluation integrity — judges dock for contamination |
| "Seventy-seven percent deterministic" | AI Judgment — the key differentiator |
| "One hundred eleven honestly reported" | Directly quotes PS-4's bar |
| "Did break. Did fix." | Closing punch for Failure Recovery |

---

## What NOT to Do

1. ❌ **Don't start with data already loaded** — the empty-to-full transition IS the demo
2. ❌ **Don't say "in production it would"** — this IS production-grade
3. ❌ **Don't rush the Gemini investigation** — let the latency prove it's real
4. ❌ **Don't skip the exception count** — 111 is the star number
5. ❌ **Don't forget "held-out test split"** — judges dock for benchmark contamination
6. ❌ **Don't read from a script** — know your numbers cold
7. ❌ **Don't say "basically" or "um"** — every second counts in 5 minutes
8. ❌ **Don't show slides or diagrams** — show the LIVE APP

---

## If You Need to Trim (Cut Order)

Cut these first (lowest judge impact):
1. Finance Chain (Scene 7) — just mention "we trace invoice to bank, there's an endpoint"
2. Human Review detail (Scene 8) — show the queue, skip the resolve action
3. Benchmark numbers (Scene 9) — reduce to 10 seconds, two numbers only

**🚫 NEVER cut:**
- Empty dashboard → upload → reconcile flow (this IS the demo)
- Exception queue + Gemini investigation (core PS-4 requirement)
- "What broke" (mandatory evaluation parameter)
- The Fix My Itch reference (your unique differentiator)
- The closing "honest exception list" line

---

## Practice Run Timing

Do 2-3 practice runs before recording. Target timings:

| Scene | Target | Danger Zone |
|---|---|---|
| Scene 1 (Hook) | 25s | If > 30s, you're rambling |
| Scene 3 (Upload) | 45s | Depends on upload speed — pause is fine |
| Scene 4 (Recon) | 45s | Don't talk over the SSE animation |
| Scene 6 (Gemini) | 45s | Don't skip the pause — latency IS the proof |
| Scene 10 (Broke) | 15s | Rapid-fire all 3 bugs — practiced delivery |
| Total | 5:00 | Hard stop at 5:00 — cut Scene 7 if needed |
