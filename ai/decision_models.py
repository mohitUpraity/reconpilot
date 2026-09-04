from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Decision = Literal["MATCH", "REVIEW", "UNRESOLVED"]

class ReconciliationDecision(BaseModel):
    """Strict, application-owned contract for an AI reconciliation recommendation."""
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    selected_payment_id: str | None = Field(default=None, max_length=128)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def decision_consistency(self) -> "ReconciliationDecision":
        if self.decision == "MATCH" and not self.selected_payment_id:
            raise ValueError("MATCH requires selected_payment_id")
        if self.decision != "MATCH" and self.selected_payment_id is not None:
            raise ValueError("Only MATCH may select a payment")
        return self

class ReconciliationPolicyError(ValueError):
    pass

def validate_business_policy(decision: ReconciliationDecision, allowed_payment_ids: set[str]) -> ReconciliationDecision:
    """Validate model output against evidence packet ownership before DB writes."""
    if decision.decision == "MATCH" and decision.selected_payment_id not in allowed_payment_ids:
        raise ReconciliationPolicyError(
            "Model selected a payment outside the evidence packet."
        )
    # The model never controls the final auto-match threshold; the controller does.
    return decision
