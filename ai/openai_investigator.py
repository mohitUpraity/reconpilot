
from __future__ import annotations
import json, os, requests

from .decision_models import ReconciliationDecision, ReconciliationPolicyError, validate_business_policy

OPENAI_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/responses")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

SYSTEM_PROMPT = """
You are ReconPilot's finance reconciliation investigator.
You investigate ambiguous invoice-to-payment relationships.

Rules:
1. Use ONLY the evidence packet.
2. Never invent identifiers, amounts, dates, customers, or links.
3. Prefer exact invoice references, amount consistency, customer identity, and plausible payment timing.
4. A recommendation is not final accounting truth.
5. If evidence is contradictory or insufficient, choose REVIEW or UNRESOLVED.
6. Return only the required structured JSON.
""".strip()

SCHEMA = {
    "type":"object",
    "properties":{
        "decision":{"type":"string","enum":["MATCH","REVIEW","UNRESOLVED"]},
        "selected_payment_id":{"type":["string","null"]},
        "confidence":{"type":"number","minimum":0,"maximum":1},
        "evidence":{"type":"array","items":{"type":"string"},"maxItems":8},
        "risks":{"type":"array","items":{"type":"string"},"maxItems":8}
    },
    "required":["decision","selected_payment_id","confidence","evidence","risks"],
    "additionalProperties":False
}

class OpenAIInvestigatorError(RuntimeError):
    pass

def investigate(evidence_packet: dict) -> dict:
    api_key=os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIInvestigatorError("OPENAI_API_KEY is not configured.")

    allowed={c["payment_id"] for c in evidence_packet.get("candidates",[])}

    body={
        "model":os.getenv("OPENAI_MODEL",DEFAULT_MODEL),
        "store":False,
        "instructions":SYSTEM_PROMPT,
        "input":[
            {
                "role":"user",
                "content":[
                    {
                        "type":"input_text",
                        "text":json.dumps(evidence_packet,separators=(",",":"))
                    }
                ]
            }
        ],
        "text":{
            "format":{
                "type":"json_schema",
                "name":"reconciliation_decision",
                "strict":True,
                "schema":SCHEMA
            }
        }
    }

    r=requests.post(
        OPENAI_URL,
        headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
        json=body,
        timeout=45
    )
    if r.status_code >= 400:
        raise OpenAIInvestigatorError(f"OpenAI API error {r.status_code}: {r.text[:1000]}")

    data=r.json()
    text=data.get("output_text")
    if not text:
        # Fallback parser for response objects where output_text is not top-level.
        parts=[]
        for item in data.get("output",[]):
            for c in item.get("content",[]):
                if c.get("type")=="output_text" and c.get("text"):
                    parts.append(c["text"])
        text="".join(parts).strip()

    if not text:
        raise OpenAIInvestigatorError("Model returned no structured output.")

    try:
        decision = ReconciliationDecision.model_validate_json(text)
    except Exception as e:
        raise OpenAIInvestigatorError(f"Structured output failed Pydantic validation: {e}") from e

    try:
        decision = validate_business_policy(decision, allowed)
    except ReconciliationPolicyError as e:
        raise OpenAIInvestigatorError(str(e)) from e

    return {
        "decision":decision.decision,
        "selected_payment_id":decision.selected_payment_id,
        "confidence":round(decision.confidence,4),
        "evidence":[str(x)[:300] for x in decision.evidence[:8]],
        "risks":[str(x)[:300] for x in decision.risks[:8]],
        "provider":"openai",
        "model":os.getenv("OPENAI_MODEL",DEFAULT_MODEL),
        "response_id":data.get("id")
    }
