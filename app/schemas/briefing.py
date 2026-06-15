from datetime import datetime
from pydantic import BaseModel


class BriefingAttentionItem(BaseModel):
    capture_id: str
    source: str
    priority: str | None
    category: str | None
    reason: str | None
    preview: str
    attention_score: float


class BriefingResponse(BaseModel):
    emails_received_today: int
    require_attention: int
    critical_count: int
    high_count: int
    top_attention: list[BriefingAttentionItem]
    generated_at: datetime
