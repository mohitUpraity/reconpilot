# Phase 9 — AI investigator

## What is now implemented
- Real OpenAI Responses API adapter.
- Strict JSON Schema Structured Outputs.
- `store=false` in the API request.
- Evidence packet limited to the case and its top candidate payments.
- Payment ID allow-list validation.
- Pydantic validation + application business-policy gate.
- Fail-closed fallback to human `REVIEW` if the live LLM call fails.
- Offline deterministic investigator for reproducible local benchmarks.
- Phase 9 batch result + ground-truth evaluator.

## Important architecture
The model is an investigator, not the accounting authority.

`financial_records → candidate evidence → AI investigator → validation → policy gate → reconciliation/review`

The model cannot:
- see `ground_truth_private.csv`
- invent payment IDs
- directly modify financial records
- convert a low-confidence answer into an automatic close

## Live mode
Set:
```bash
export OPENAI_API_KEY=...
export USE_LIVE_LLM=true
export OPENAI_MODEL=...
```

Then:
```bash
python scripts/run_ai_controller.py
python scripts/evaluate_phase9.py
```

The local benchmark defaults to `USE_LIVE_LLM=false` so it remains deterministic.

Pydantic validation is applied to live structured output before business-policy checks.

OpenAI's current API documentation recommends Structured Outputs with `json_schema` for strict JSON structure; the Responses API supports `text.format` for this configuration.


## Current benchmark status
The packaged benchmark is OFFLINE / deterministic. It is useful for pipeline regression and ground-truth evaluation, but it is not evidence of a live LLM improvement.

For the final competition report:
1. Keep the hidden test set private.
2. Run the live LLM only on the held-out inference cases.
3. Save model name, prompt version, schema version and timestamp.
4. Evaluate the resulting predictions against the hidden test set.
5. Report both baseline and AI-assisted metrics.
