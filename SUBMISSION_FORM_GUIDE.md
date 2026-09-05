# Razorpay AI Buildathon — Submission Form Guide

> **Form URL:** https://forms.gle/d9r2gvxp8cmoZhon9
> **Deadline:** September 5, 2026
> **DO NOT submit until your video is uploaded and repo is public**

---

## Form Structure (3 Pages, 10 Fields)

---

### PAGE 1: Basic Information

| # | Field | Type | Required | Your Answer |
|---|---|---|---|---|
| 1 | **Email** | Text | Yes | _your email_ |
| 2 | **Full Name** | Text | Yes | _your name_ |
| 3 | **College Name** | Text | Yes | _your college_ |
| 4 | **Graduation Year** | Dropdown | Yes | `2027` / `2028` / `2029` |
| 5 | **In-person Internship availability starting September** | Radio | Yes | `Yes` / `No` |

> You MUST select **Yes** for in-person availability (Bangalore) to qualify.

---

### PAGE 2: Internship Details

| # | Field | Type | Required | Your Answer |
|---|---|---|---|---|
| 6 | **Preferred Internship Duration** | Radio | Yes | `6-Month Internship` / `12-Month Internship` |

---

### PAGE 3: Final Submission (The Important Part)

| # | Field | Type | Required |
|---|---|---|---|
| 7 | **GitHub Repository URL** | Text | Yes |
| 8 | **5-min Pitch Video Link** | Text | Yes |
| 9 | **Build Challenges & Technical Obstacles** | Long Text | Yes |
| 10 | **Final Submission Confirmation** | Checkbox | Yes |

---

## Pre-Filled Draft Answers

### Field 7: GitHub Repository URL

```
https://github.com/<your-username>/reconpilot
```

> Make sure the repo is **PUBLIC** before submitting. Judges will clone and run it.

---

### Field 8: 5-min Pitch Video Link

```
https://youtu.be/<your-video-id>
```

> Upload as **Unlisted** on YouTube. Test the link in an incognito window before submitting.

---

### Field 9: Build Challenges & Technical Obstacles

> This is the **"What Broke at 2 AM"** field. Copy-paste and customize:

```
CHALLENGE 1: Silent Zero in Exception Queue
The Exception Queue UI showed 0 exceptions instead of 111. No visible error.
Root cause: JavaScript variable scope bug — `rows` was used without declaration
in the fetch callback, causing a ReferenceError that was silently swallowed.
Fix: Explicit `let rows = d.items || []` declaration.
Why it matters: This is exactly the class of silent failure ReconPilot is built
to prevent — a finance dashboard showing "all clear" when 111 cases need attention.

CHALLENGE 2: Inflated Exception Count (642 vs 111)
After running all reconciliation stages, exception count jumped to 642.
Root cause: The payment-to-settlement reconciliation stage ran before settlement
data was fully imported, generating 531 spurious "no matching settlement" exceptions.
Fix: Enforced sequential stage ordering in the batch script — import all sources
first, then run invoice->payment, then payment->settlement, then settlement->bank.
Diagnosed by: SELECT case_type, COUNT(*) FROM exceptions GROUP BY case_type;

CHALLENGE 3: Gemini 429 Rate Limit Cascade
Batch AI investigation of 111 cases crashed after ~15 calls with 429 Too Many Requests.
Root cause: Free Gemini tier allows 15 RPM. No pacing was implemented.
Fix: Built a rate guard with 4.2-second inter-call delay (14.28 RPM, safely under
15 RPM). Added 3-attempt retry with Retry-After header respect and model fallback
chain: gemini-2.5-flash-lite -> gemini-2.0-flash -> gemini-1.5-flash.

CHALLENGE 4: Pydantic Hallucination Guard
Early Gemini responses included extra fields like "reasoning" and "alternative_matches"
that weren't in our schema. Without `extra='forbid'`, these silently passed validation.
Fix: Added ConfigDict(extra="forbid") to the Pydantic model, plus a model_validator
that rejects MATCH decisions without a payment_id and non-MATCH decisions with one.
```

---

### Field 10: Final Submission Confirmation

> Check the box: **"I confirm that this is my official final project submission. I understand that no further changes or edits can be made after submitting."**

---

## Pre-Submission Checklist

- [ ] **Repo is PUBLIC** on GitHub
- [ ] **README.md** has architecture diagrams, benchmark numbers, setup instructions
- [ ] **Video uploaded** as Unlisted on YouTube (test link in incognito)
- [ ] **Server runs** — clone from scratch works: `pip install && uvicorn` -> opens
- [ ] **Tests pass** — `pytest -q` shows 10 passed
- [ ] **API key works** — `curl /api/v1/ai/status` shows `has_key: true`
- [ ] **DB has data** — `curl /api/v1/overview/merchant_demo` shows correct counts
- [ ] **Video is under 5 minutes**
- [ ] **"Build Challenges" field is filled** — not blank, has real technical detail
- [ ] **Graduation Year is correct**
- [ ] **In-person = Yes**
- [ ] You have **clicked the confirmation checkbox**

---

## What Judges Will Do After You Submit

1. **Read your README** — architecture, benchmark, story, compliance checklist
2. **Watch your video** — they will NOT watch past 5 minutes
3. **Clone your repo** — they WILL try to run it locally
4. **Read your "Build Challenges"** answer — this is the "what broke at 2 AM" parameter
5. **Check for AI Judgment** — did you force AI everywhere or use it only where needed?
6. **Look at the exception list** — PS-4 explicitly requires honest reporting

---

## Evaluation Parameters (How Judges Score)

| Parameter | Weight | What They Check | ReconPilot Evidence |
|---|---|---|---|
| **Problem Taste** | High | Real finance problem, meaningful scale | 500 invoices, 4-source recon, full invoice-to-bank loop |
| **Build Quality** | High | Clean code, tests pass, actually runs | 10 tests, 17 endpoints, modular architecture, FK constraints |
| **AI Judgment** | High | AI only where needed, not forced | Tier 1 handles 77.8% at $0. AI only for 22.2% ambiguous cases |
| **Failure Recovery** | High | What broke, how you fixed it | 3 real bugs with before/after code, SQL diagnosis queries |

---

## Timeline for Today (September 5)

| Time | Action |
|---|---|
| Now | Finalize README, push to GitHub (public) |
| +30 min | Record 5-min video (use VIDEO_DEMO_SCRIPT.md) |
| +1 hour | Upload video to YouTube (Unlisted), test link |
| +1.5 hours | Fill form, paste GitHub URL + video link |
| +1.5 hours | Copy "Build Challenges" text from above |
| +1.5 hours | Check confirmation box |
| +1.5 hours | **SUBMIT** |
| +2 hours | Verify: re-open form link to confirm submission went through |

---

*Good luck. Your code speaks louder than your resume.*
