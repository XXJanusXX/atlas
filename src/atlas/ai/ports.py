from typing import Protocol

from pydantic import BaseModel


class SignalReview(BaseModel):
    model_name: str
    recommendation: str
    confidence: float
    rationale: str


class AIReviewer(Protocol):
    async def review_signal(self, signal_payload: dict[str, object]) -> SignalReview: ...


# AI reviewers are advisory only and receive no execution capability.
