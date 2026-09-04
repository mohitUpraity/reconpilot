from __future__ import annotations
from pathlib import Path
import json, os, requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .decision_models import ReconciliationDecision, ReconciliationPolicyError, validate_business_policy

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

SYSTEM_PROMPT = """
You are ReconPilot's finance reconciliation investigator.
You investigate ambiguous invoice-to-payment relationships for merchants.

Rules:
1. Use ONLY the provided evidence packet.
2. Never invent identifiers, amounts, dates, customer names, or links.
3. Prefer exact invoice references, amount consistency, customer identity matching, and plausible payment timing.
4. A recommendation is NOT final accounting truth; human review or policy gate will verify.
5. If evidence is contradictory or insufficient, choose REVIEW or UNRESOLVED.
6. Return only structured JSON matching the specified schema.
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

def investigate(evidence_packet: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise GeminiInvestigatorError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured in environment or .env.")

    allowed = {c["payment_id"] for c in evidence_packet.get("candidates", [])}
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

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

    try:
        r = requests.post(url, json=body, timeout=45)
    except Exception as exc:
        raise GeminiInvestigatorError(f"Network error connecting to Gemini API: {exc}") from exc

    if r.status_code >= 400:
        raise GeminiInvestigatorError(f"Gemini API error {r.status_code}: {r.text[:800]}")

    data = r.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise GeminiInvestigatorError("Gemini API returned no candidates.")

    first_cand = candidates[0]
    parts = first_cand.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise GeminiInvestigatorError("Gemini returned empty text response.")

    try:
        decision = ReconciliationDecision.model_validate_json(text)
    except Exception as e:
        raise GeminiInvestigatorError(f"Gemini output failed Pydantic validation: {e}") from e

    try:
        decision = validate_business_policy(decision, allowed)
    except ReconciliationPolicyError as e:
        raise GeminiInvestigatorError(str(e)) from e

    return {
        "decision": decision.decision,
        "selected_payment_id": decision.selected_payment_id,
        "confidence": round(decision.confidence, 4),
        "evidence": [str(x)[:300] for x in decision.evidence[:8]],
        "risks": [str(x)[:300] for x in decision.risks[:8]],
        "provider": "gemini",
        "model": model,
        "raw_json": text
    }
