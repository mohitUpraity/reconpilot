
from __future__ import annotations
import json, os
from .openai_investigator import investigate as openai_investigate, OpenAIInvestigatorError

def offline_investigate(packet:dict)->dict:
    cands=packet.get("candidates",[])
    if not cands:
        return {
            "decision":"UNRESOLVED","selected_payment_id":None,"confidence":0,
            "evidence":[],"risks":["No candidate payments available."],
            "provider":"offline","model":"evidence-policy-v1"
        }
    best=cands[0]
    second=cands[1] if len(cands)>1 else None
    margin=float(best["score"])-(float(second["score"]) if second else 0)
    sig=best["signals"]
    evidence=[]; risks=[]

    if sig.get("reference_exact"):
        evidence.append("Normalized invoice reference exactly matches candidate.")
    else:
        risks.append("No exact invoice reference match.")

    if sig.get("amount_exact"):
        evidence.append("Payment amount exactly matches invoice amount.")
    elif sig.get("amount_ratio",0)>=.98:
        risks.append("Payment amount is close but not exact.")
    else:
        risks.append("Payment amount materially differs.")

    cs=float(sig.get("customer_similarity",0))
    if cs>=.90: evidence.append("Customer identity has very high similarity.")
    elif cs>=.75: evidence.append("Customer identity is similar but not conclusive.")
    else: risks.append("Customer identity similarity is weak.")

    dd=int(sig.get("date_distance_days",999))
    if dd<=7: evidence.append("Payment timing is close to the invoice date.")
    elif dd<=30: risks.append("Payment is relatively far from invoice date.")
    else: risks.append("Payment timing is outside the normal window.")

    if sig.get("reference_exact") and sig.get("amount_exact") and cs>=.90:
        return {"decision":"MATCH","selected_payment_id":best["payment_id"],
                "confidence":.985,"evidence":evidence,"risks":risks,
                "provider":"offline","model":"evidence-policy-v1"}
    if float(best["score"])>=.78 and margin>=.10:
        return {"decision":"MATCH","selected_payment_id":best["payment_id"],
                "confidence":round(min(.95,float(best["score"])+.05),4),
                "evidence":evidence,"risks":risks,
                "provider":"offline","model":"evidence-policy-v1"}
    if float(best["score"])>=.62:
        return {"decision":"REVIEW","selected_payment_id":None,
                "confidence":round(float(best["score"]),4),
                "evidence":evidence,"risks":risks or ["Ambiguous evidence."],
                "provider":"offline","model":"evidence-policy-v1"}
    return {"decision":"UNRESOLVED","selected_payment_id":None,
            "confidence":round(float(best["score"]),4),
            "evidence":evidence,"risks":risks or ["Insufficient evidence."],
            "provider":"offline","model":"evidence-policy-v1"}

def investigate(packet:dict, live:bool|None=None)->dict:
    if live is None:
        live=os.getenv("USE_LIVE_LLM","false").lower()=="true"
    if live:
        try:
            return openai_investigate(packet)
        except OpenAIInvestigatorError:
            # Fail closed: do not fabricate a finance decision when the model is unavailable.
            return {
                "decision":"REVIEW",
                "selected_payment_id":None,
                "confidence":0,
                "evidence":[],
                "risks":["Live AI investigation failed; case routed to human review."],
                "provider":"fallback",
                "model":"none"
            }
    return offline_investigate(packet)
