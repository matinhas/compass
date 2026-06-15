from pydantic import BaseModel


class DashboardTopItem(BaseModel):
    capture_id: str
    content_preview: str
    priority: str | None
    source_type: str | None
    attention_score: float


class DashboardAttentionItem(BaseModel):
    capture_id: str
    source: str
    title: str
    priority: str | None
    attention_score: float
    reason: str | None
    category: str | None


class DashboardResponse(BaseModel):
    # Executive summary
    critical_count: int
    high_count: int
    captures_today: int
    # Actionable attention items
    attention_items: list[DashboardAttentionItem]
    # Scored ranking
    top_attention: list[DashboardTopItem]
    # Roadmap
    current_focus: str
    active_commitments: int
    completed_milestones: int
    roadmap_progress: int
    # Breakdown
    source_breakdown: dict[str, int]
    domain_breakdown: dict[str, int]
    # System
    system_health: str
    generated_at: str
