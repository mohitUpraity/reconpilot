from __future__ import annotations
from pathlib import Path
import json, os, time, requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .decision_models import ReconciliationDecision, ReconciliationPolicyError, validate_business_policy

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]

SYSTEM_PROMPT = """
You are ReconPilot's finance reconciliation investigator.
You investigate ambiguous invoice-to-payment relationships for merchants.

Rules:
1. Use ONLY the provided evidence packet.
2. Never invent identifiers, amounts, dates, customer names, or links.
3. Prefer exact invoice references, amount consistency, customer identity matching, and plausible payment timing.
4. A recommendation is NOT final accounting truth; human review or policy gate will verify.
5. If evidence is contradictory or insufficient, choose REVIEW or UNRESOLVED.
6. If decision is 'REVIEW' or 'UNRESOLVED', selected_payment_id MUST be null. Only set selected_payment_id when decision is 'MATCH'.
7. Return only structured JSON matching the specified schema.
""".strip()

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["MATCH", "REVIEW", "UNRESOLVED"]},
        "selected_payment_id": {"type": "string", "nullable": True},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "risks": {"type": "array", "items": {"type": "string"}, "maxItems": 8}
    },
    "required": ["decision", "selected_payment_id", "confidence", "evidence", "risks"]
}

class GeminiInvestigatorError(RuntimeError):
    pass

def test_connection() -> dict:
    """Tests live Gemini connectivity with the configured API key and models."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "GEMINI_API_KEY is not configured in .env",
            "model": os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        }

    candidate_models = [os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)] + [m for m in FALLBACK_MODELS if m != os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)]
    last_err = ""

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        body = {
            "contents": [{"parts": [{"text": "Reply only with JSON: {\"status\":\"ok\",\"service\":\"reconpilot_gemini\"}"}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.0}
        }
        t0 = time.time()
        try:
            r = requests.post(url, json=body, timeout=12)
            elapsed_ms = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                data = r.json()
                usage = data.get("usageMetadata", {})
                return {
                    "ok": True,
                    "model": model,
                    "latency_ms": elapsed_ms,
                    "usage": {
                        "prompt_tokens": usage.get("promptTokenCount", 14),
                        "candidates_tokens": usage.get("candidatesTokenCount", 10),
                        "total_tokens": usage.get("totalTokenCount", 24)
                    },
                    "note": f"Successfully verified live connection to {model}."
                }
            elif r.status_code == 404:
                last_err = f"Model {model} not found on v1beta API."
                continue
            else:
                return {
                    "ok": False,
                    "error": f"Gemini API returned status {r.status_code}: {r.text[:300]}",
                    "model": model
                }
        except Exception as exc:
            last_err = str(exc)

    return {"ok": False, "error": last_err or "Failed to connect to Gemini API."}


def investigate(evidence_packet: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise GeminiInvestigatorError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured in environment or .env.")

    allowed = {c["payment_id"] for c in evidence_packet.get("candidates", [])}
    primary_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    candidate_models = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]

    body = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Evidence packet to investigate:\n{json.dumps(evidence_packet, separators=(',', ':'))}"}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
            "temperature": 0.1
        }
    }

    last_error = ""
    data = None
    used_model = primary_model

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(3):
            try:
                r = requests.post(url, json=body, timeout=45)
                if r.status_code == 200:
                    data = r.json()
                    used_model = model
                    break
                elif r.status_code == 429:
                    wait_sec = int(r.headers.get("Retry-After", 5 * (attempt + 1)))
                    time.sleep(wait_sec)
                    last_error = f"Gemini 429 Rate Limit encountered. Automatically backed off for {wait_sec}s (Attempt {attempt+1}/3)."
                    continue
                elif r.status_code == 404:
                    last_error = f"Model {model} not found (404). Trying next compatible model..."
                    break
                else:
                    raise GeminiInvestigatorError(f"Gemini API error {r.status_code}: {r.text[:800]}")
            except requests.RequestException as exc:
                last_error = f"Network error connecting to Gemini ({model}): {exc}"
                break

        if data:
            break

    if not data:
        raise GeminiInvestigatorError(f"All candidate Gemini models failed. Last error: {last_error}")

    candidates = data.get("candidates", [])
    if not candidates:
        raise GeminiInvestigatorError("Gemini API returned no candidates.")

    first_cand = candidates[0]
    parts = first_cand.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise GeminiInvestigatorError("Gemini returned empty text response.")

    try:
        parsed_json = json.loads(text)
        if parsed_json.get("decision") != "MATCH" and parsed_json.get("selected_payment_id"):
            cand_id = parsed_json.get("selected_payment_id")
            parsed_json["selected_payment_id"] = None
            ev_list = parsed_json.get("evidence", [])
            if isinstance(ev_list, list):
                ev_list.append(f"Candidate {cand_id} analyzed and held for manual review.")
                parsed_json["evidence"] = ev_list
        decision = ReconciliationDecision.model_validate(parsed_json)
    except Exception as e:
        raise GeminiInvestigatorError(f"Gemini output failed Pydantic validation: {e}") from e

    try:
        decision = validate_business_policy(decision, allowed)
    except ReconciliationPolicyError as e:
        raise GeminiInvestigatorError(str(e)) from e

    usage = data.get("usageMetadata", {})
    prompt_tokens = usage.get("promptTokenCount", 0)
    cand_tokens = usage.get("candidatesTokenCount", 0)
    total_tokens = usage.get("totalTokenCount", prompt_tokens + cand_tokens)
    # Gemini Flash-Lite pricing: ~$0.10 / 1M input tokens, ~$0.40 / 1M output tokens
    est_cost_usd = round(((prompt_tokens * 0.10) + (cand_tokens * 0.40)) / 1_000_000, 7)

    return {
        "decision": decision.decision,
        "selected_payment_id": decision.selected_payment_id,
        "confidence": round(decision.confidence, 4),
        "evidence": [str(x)[:300] for x in decision.evidence[:8]],
        "risks": [str(x)[:300] for x in decision.risks[:8]],
        "provider": "gemini",
        "model": used_model,
        "raw_json": text,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "candidates_tokens": cand_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": est_cost_usd
        }
    }
