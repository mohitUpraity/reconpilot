
from typing import Any
from pydantic import BaseModel, Field

class WebhookEnvelope(BaseModel):
    event_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    payload: dict[str, Any]

class ReviewResolution(BaseModel):
    action: str = Field(pattern="^(approve_match|reject)$")
    payment_id: str | None = Field(default=None, max_length=128)
    note: str = Field(default="", max_length=500)
    actor: str = Field(default="human_reviewer", min_length=1, max_length=100)
