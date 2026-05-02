"""
Shared enums and Pydantic models for the triage pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    feature_request = "feature_request"
    account = "account"
    integration = "integration"
    onboarding = "onboarding"
    security = "security"
    performance = "performance"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


VALID_CATEGORIES: frozenset[str] = frozenset(c.value for c in Category)
VALID_PRIORITIES: frozenset[str] = frozenset(p.value for p in Priority)


class Ticket(BaseModel):
    """Normalised representation of an incoming ticket."""

    ticket_id: str
    customer_name: str = ""
    plan: str = ""
    subject: str
    body: str

    @field_validator(
        "ticket_id", "customer_name", "plan", "subject", "body",
        mode="before",
    )
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class KBEntry(BaseModel):
    """One row from the knowledge base CSV."""

    ticket_id: str
    customer_name: str = ""
    plan: str = ""
    subject: str
    body: str
    category: str
    priority: str
    resolution: str = ""

    @field_validator("category", "priority", mode="before")
    @classmethod
    def normalise_lower(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator(
        "ticket_id",
        "customer_name",
        "plan",
        "subject",
        "body",
        "resolution",
        mode="before",
    )
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class TriageResult(BaseModel):
    """Pipeline output for a single ticket."""

    ticket_id: str
    category: str
    priority: str
    response: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        out = self.model_dump(exclude_none=True)
        # Always include flags even when empty
        out.setdefault("flags", [])
        return out
