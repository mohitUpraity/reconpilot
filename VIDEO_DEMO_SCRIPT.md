# 🎬 ReconPilot — 5-Minute Video Demo Script

> **Target audience:** Razorpay Buildathon judges
> **Track:** 04 — AI Finance Controller
> **Total runtime:** 5 minutes (300 seconds)
> **Tone:** Confident, technical, story-driven. No filler. Every second counts.

---

## ⏱️ Timeline Overview

| Timestamp | Scene | Duration |
|---|---|---|
| 0:00 – 0:30 | Hook — The Pain | 30s |
| 0:30 – 1:00 | One-Line Solution + Architecture | 30s |
| 1:00 – 1:50 | Live Demo — Control Room | 50s |
| 1:50 – 2:30 | Demo — Run the Reconciliation Stream | 40s |
| 2:30 – 3:10 | Demo — Exception Queue + AI Investigation | 40s |
| 3:10 – 3:40 | Demo — Finance Chain (Invoice → Bank) | 30s |
| 3:40 – 4:10 | Demo — Human Review + Audit Trail | 30s |
| 4:10 – 4:40 | Benchmark Numbers + Governance | 30s |
| 4:40 – 5:00 | Closing Statement | 20s |

---

## 🎙️ Scene 1 — Hook: The Pain (0:00 – 0:30)

### What to show on screen:
- Terminal. Run: `curl http://127.0.0.1:8000/api/v1/overview/merchant_demo`
- Show the JSON response: `"financial_records": 1655, "reconciliation_cases": 1031, "exceptions": 111`

### What to say:
> "Every month-end, a merchant's finance team opens a spreadsheet.
> Five hundred invoices. Five hundred thirty-one Razorpay payments.
> Seventy-six settlements. Eighty-one bank credits.
> And the question: which invoice matches which payment?
> Which settlement actually landed in the bank?
> This takes six hours, two analysts — and still has errors.
> ReconPilot eliminates that. Completely."

---

## 🎙️ Scene 2 — Solution + Architecture (0:30 – 1:00)

### What to show on screen:
- Browser: `http://127.0.0.1:8000` — Control Room landing page
- Point at the KPI bar: 1,655 records, 1,031 cases, 111 exceptions

### What to say:
> "ReconPilot is a three-tier AI Finance Controller built on FastAPI, SQLite, and Google Gemini.
> Tier One: deterministic SQL rules. Instant. Free. Handles seventy-seven percent of cases.
> Tier Two: a calibrated confidence gate at zero-point-nine-three — tuned on a held-out validation split.
> Tier Three: live Gemini AI — with Pydantic strict validation, a policy gate, and a full audit trail.
> This is not a chatbot wrapper. This is production-grade governance."

---

## 🎙️ Scene 3 — Live Demo: Control Room (1:00 – 1:50)

### What to show on screen:
- Scroll through the **Control Room** tab slowly
- Point out the four pipeline nodes: Ingest → Match → AI Route → Resolve
- Point out the case status cards: RECONCILED 389, REVIEW 73, UNRESOLVED 38

### What to say:
> "This is the Control Room. Every number you see is live — pulled from SQLite in real time.
> Eighteen hundred fifty-five financial records across four sources: invoices, Razorpay payments, settlements, and bank statement.
> Three hundred eighty-nine cases automatically reconciled — zero AI cost, under ten milliseconds.
> Seventy-three in human review. Thirty-eight unresolved. One hundred eleven exceptions — the hard cases.
> Nothing is hardcoded. Refresh the page and the numbers come from the database."

---

## 🎙️ Scene 4 — Demo: Reconciliation Stream (1:50 – 2:30)

### What to show on screen:
- Click **"Run Demo"** button (or equivalent on the control room page)
- Watch the SSE streaming animation play — 9 steps
- Show steps flowing: Ingest → Normalize → Scan → Deterministic → AI Route → AI Investigate → Policy Gate → Human Queue → Complete

### What to say:
> "Watch the reconciliation cycle run live.
> Step one: four financial sources detected.
> Step two: one thousand one hundred ninety records normalized.
> Step three: five hundred invoice cases scanned.
> Step four: the deterministic engine resolves three hundred eighty-nine instantly.
> Step five: one hundred eleven ambiguous cases routed to AI.
> Step six: Gemini proposes matches, reviews, and unresolved cases.
> Step seven: the policy gate runs — blocks anything under zero-point-nine-three confidence.
> Step eight: seventy-three cases queued for human review.
> This is real Server-Sent Events — not a fake animation."

---

## 🎙️ Scene 5 — Demo: Exception Queue + AI Investigation (2:30 – 3:10)

### What to show on screen:
- Navigate to **Exception Queue** tab
- Show the list: 111 exceptions with severity, case type, confidence, reason
- Click on one exception to open the **Case Detail Drawer**
- Click **"Investigate with Gemini"** button
- Show the live AI response: decision, confidence, evidence bullets, risks

### What to say:
> "Here's the exception queue — one hundred eleven cases where evidence was insufficient or conflicting.
> These were never silently closed. Every one is here, in the queue, waiting for action.
> Let's click one. This is an invoice-to-payment case — amount matches, but the reference doesn't align.
> I'll trigger a live Gemini investigation now.
> [wait for response]
> Gemini returns structured JSON: decision, confidence, evidence bullets, risk factors.
> The output is validated by Pydantic with extra-equals-forbid — any hallucinated field fails hard.
> The policy gate then checks that the selected payment ID is actually inside the evidence packet.
> Three layers of governance before a single write touches the database."

---

## 🎙️ Scene 6 — Demo: Finance Chain (3:10 – 3:40)

### What to show on screen:
- Navigate to **Finance Chain** tab or call: `curl http://127.0.0.1:8000/api/v1/chain/CASE-001`
- Show the four-node chain: Invoice → Payment → Settlement → Bank
- Highlight fee deduction: gross ₹42,800 → net ₹42,419 after Razorpay fees

### What to say:
> "One of the biggest reconciliation headaches: the settlement amount never equals the invoice amount.
> Razorpay deducts fees and GST before crediting to the bank.
> This is the Finance Chain view. One API call shows the complete money trail:
> Invoice issued for forty-two thousand eight hundred rupees.
> Payment captured at full amount.
> Settlement batched — three hundred twelve rupees fee, sixty-nine rupees GST — net amount forty-two thousand four hundred nineteen rupees.
> Bank credited with the UTR reference.
> Fully traced. Fully auditable. No spreadsheet required."

---

## 🎙️ Scene 7 — Demo: Human Review + Audit Trail (3:40 – 4:10)

### What to show on screen:
- Navigate to **Human Review** tab — show the 73 cases
- Click one case. Show the **Resolve** action (Approve / Reject / Override with note)
- Navigate to **Audit Trail** tab — show the immutable event log with actor, timestamp, AI model

### What to say:
> "Seventy-three cases need a human eye. Analyst opens a case, sees the AI recommendation and evidence, and can approve, reject, or override with a note.
> Every action writes an immutable audit event — who acted, what AI model was used, what confidence score triggered the routing.
> This is the Human-in-the-Loop that Problem Statement Four asks for.
> Not just a queue — a full governance record that would satisfy a financial regulator."

---

## 🎙️ Scene 8 — Benchmark Numbers + Governance (4:10 – 4:40)

### What to show on screen:
- Navigate to **Benchmark & Policy** tab
- Show the three-tier architecture table
- Highlight: Tier 1 Precision 100%, Tier 2 Precision 96.61%, F1 84.44% on held-out test split

### What to say:
> "Let's talk numbers. On the held-out test split — eighty-eight cases the model never saw during calibration —
> precision is ninety-six-point-six percent. F1 is eighty-four-point-four.
> Tier One handles seventy-seven-point-eight percent of cases at one hundred percent precision and zero cost.
> Tier Three — Gemini — operates within the free tier: fourteen-point-two-eight requests per minute, four-hundred-seventy requests per day safe cap.
> Each investigation costs roughly zero-point-zero-zero-zero-one-six-five US dollars.
> Total cost for all one hundred eleven exceptions: under two cents.
> The ground truth file was never passed to the model, never shown in the UI, and the test split was never used for threshold tuning.
> These numbers are real."

---

## 🎙️ Scene 9 — Closing Statement (4:40 – 5:00)

### What to show on screen:
- Return to Control Room homepage
- Run in terminal: `pytest -q` → show `10 passed`

### What to say:
> "ReconPilot is a production-grade AI Finance Controller — not a demo stub.
> Real Razorpay API integration. Real Gemini AI. Real governance.
> Ten tests passing. Seventeen REST endpoints. One control room.
> Track Four. Problem Statement Four. ReconPilot."

---

## 🎯 Key Talking Points — Cheat Sheet

If you need to trim, cut in this priority order (lowest impact first):
1. Finance Chain scene (3:10–3:40) → just mention it exists, don't demo
2. Audit Trail (3:40–4:10) → skip the resolve action, just show the log
3. Benchmark scene → reduce to 20 seconds, key numbers only

**Never cut:**
- The SSE demo stream (shows real-time, not fake)
- The Gemini investigation + Pydantic governance (core PS4 requirement)
- The 10 tests passing (verifiability requirement)

---

## 🔴 Things to Emphasize for Judges

| Talking Point | Why It Matters |
|---|---|
| "Not hardcoded — live SQLite" | Proves data integrity |
| "Pydantic extra='forbid'" | Shows AI hallucination guard |
| "Policy gate checks evidence packet ownership" | Shows safety beyond Pydantic |
| "Ground truth never seen by the model" | Shows evaluation integrity |
| "14.28 RPM — under the 15 RPM free tier limit" | Shows rate compliance |
| "10 tests passing" | Shows code quality |
| "HMAC-SHA256 webhook verification" | Shows Razorpay integration depth |
| "Human-in-the-Loop queue" | Directly addresses PS4 |

---

## 🛑 Common Demo Mistakes — Avoid These

1. **Don't start with setup** — server should already be running before you hit record
2. **Don't skip the exception count** — 111 is the star number, tie it to the AI routing
3. **Don't say "this would" or "in production it would"** — the demo IS production-grade
4. **Don't rush the Gemini investigation** — let it load live, the latency proves it's real
5. **Don't forget to say "held-out test split"** — judges will dock points for benchmark contamination if not mentioned

---

## 🎬 Pre-Recording Checklist

```bash
# 1. Server running
uvicorn api.app:app --reload --port 8000

# 2. Verify DB state
curl http://127.0.0.1:8000/api/v1/overview/merchant_demo
# expect: financial_records=1655, reconciliation_cases=1031, exceptions=111

# 3. Verify AI key works
curl http://127.0.0.1:8000/api/v1/ai/status
# expect: has_key=true

# 4. Run tests one last time
pytest -q
# expect: 10 passed

# 5. Open browser to http://127.0.0.1:8000 — Control Room ready
```

---

*ReconPilot · Razorpay AI Buildathon 2025 · Track 04 · Problem Statement 4*
