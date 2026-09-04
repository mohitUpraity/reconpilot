import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from pydantic import ValidationError
from ai.decision_models import ReconciliationDecision, ReconciliationPolicyError, validate_business_policy


def test_valid_match():
    d = ReconciliationDecision(
        decision="MATCH",
        selected_payment_id="pay_001",
        confidence=0.91,
        evidence=["Exact reference"],
        risks=[]
    )
    assert d.selected_payment_id == "pay_001"


def test_match_requires_payment_id():
    with pytest.raises(ValidationError):
        ReconciliationDecision(
            decision="MATCH", selected_payment_id=None, confidence=0.9,
            evidence=[], risks=[]
        )


def test_non_match_cannot_select_payment():
    with pytest.raises(ValidationError):
        ReconciliationDecision(
            decision="REVIEW", selected_payment_id="pay_001", confidence=0.6,
            evidence=[], risks=["Ambiguous"]
        )


def test_confidence_must_be_0_to_1():
    with pytest.raises(ValidationError):
        ReconciliationDecision(
            decision="REVIEW", selected_payment_id=None, confidence=1.2,
            evidence=[], risks=[]
        )


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        ReconciliationDecision.model_validate({
            "decision":"REVIEW", "selected_payment_id":None, "confidence":0.4,
            "evidence":[], "risks":[], "accounting_entry":"approve"
        })


def test_hallucinated_payment_id_is_rejected_by_business_policy():
    d = ReconciliationDecision(
        decision="MATCH", selected_payment_id="pay_not_in_packet", confidence=0.99,
        evidence=["Looks exact"], risks=[]
    )
    with pytest.raises(ReconciliationPolicyError):
        validate_business_policy(d, {"pay_001", "pay_002"})
