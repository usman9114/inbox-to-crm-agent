import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Intent = Literal["sales_lead", "support", "invoice", "spam", "other"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailIn(BaseModel):
    """Incoming message. Rejected with HTTP 422 when it cannot be processed."""

    subject: str = ""
    body: str
    sender: str = Field(alias="from")

    model_config = {"populate_by_name": True}

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("body is empty")
        return v

    @field_validator("sender")
    @classmethod
    def sender_is_email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_RE.match(v):
            raise ValueError("'from' is not a valid email address")
        return v


class Extraction(BaseModel):
    """What the LLM must return (used as the tool / JSON schema)."""

    intent: Intent = Field(description="sales_lead, support, invoice, spam or other")
    confidence: float = Field(ge=0, le=1, description="0-1, how sure you are about the intent and the fields")
    company: Optional[str] = Field(None, description="Company or organisation of the sender, null if not stated")
    contact_name: Optional[str] = Field(None, description="Person's name, null if not stated")
    email: Optional[str] = Field(None, description="Best reply-to email address")
    phone: Optional[str] = Field(None, description="Phone number as written, null if absent")
    budget: Optional[str] = Field(None, description="Budget or amount of money mentioned, as written")
    timeline: Optional[str] = Field(None, description="Deadline or time frame mentioned, as written")
    product_interest: Optional[str] = Field(None, description="Product or service the sender is interested in or writing about")
    urgency: int = Field(ge=1, le=5, description="1 = no rush, 5 = needs action today")
    summary: str = Field(max_length=300, description="One-line summary, max 25 words")

    @field_validator("company", "contact_name", "email", "phone", "budget", "timeline", "product_interest", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str) and (not v.strip() or v.strip().lower() in {"null", "none", "n/a", "unknown"}):
            return None
        return v


class ExtractionOut(Extraction):
    needs_review: bool
    review_reasons: list[str] = []
    route: Literal["lead", "review", "other"]
    hot: bool
    model: str
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0


REVIEW_CONFIDENCE = 0.7


def review_reasons(x: Extraction) -> list[str]:
    """Business rules applied on top of the schema. Any reason routes the email to human review."""
    reasons = []
    if x.confidence < REVIEW_CONFIDENCE:
        reasons.append(f"confidence {x.confidence:.2f} < {REVIEW_CONFIDENCE}")
    if x.email and not EMAIL_RE.match(x.email):
        reasons.append("extracted email is not a valid address")
    if x.intent == "sales_lead":
        if not x.email and not x.phone:
            reasons.append("sales lead without any contact detail")
        if not x.company and not x.contact_name:
            reasons.append("sales lead without company or contact name")
    return reasons
