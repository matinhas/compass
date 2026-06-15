from datetime import datetime
from pydantic import BaseModel

from app.schemas.capture import CaptureResponse


class ScoreBreakdown(BaseModel):
    priority: float
    capture_type: float
    recency: float
    confidence_factor: float


class AttentionItem(BaseModel):
    capture: CaptureResponse
    attention_score: float
    score_breakdown: ScoreBreakdown


class AttentionResponse(BaseModel):
    ranked: list[AttentionItem]
    generated_at: datetime
