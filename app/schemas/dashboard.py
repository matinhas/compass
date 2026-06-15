from pydantic import BaseModel


class DashboardTopItem(BaseModel):
    capture_id: str
    content_preview: str
    priority: str | None
    source_type: str | None
    attention_score: float


class DashboardResponse(BaseModel):
    critical_count: int
    high_count: int
    captures_today: int
    source_breakdown: dict[str, int]
    domain_breakdown: dict[str, int]
    top_attention: list[DashboardTopItem]
    generated_at: str
    current_focus: str
    active_commitments: int
    completed_milestones: int
