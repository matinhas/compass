from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.capture import Capture
from app.schemas.attention import AttentionItem, AttentionResponse, ScoreBreakdown
from app.schemas.capture import CaptureResponse

_PRIORITY_SCORES: dict[str, float] = {
    "Critical": 50.0,
    "High": 35.0,
    "Normal": 15.0,
    "Low": 5.0,
}

_TYPE_SCORES: dict[str, float] = {
    "Alert": 20.0,
    "Task": 10.0,
    "Decision": 10.0,
    "Project": 5.0,
    "Reference": 0.0,
}

_RECENCY_MAX = 20.0
_RECENCY_HALF_LIFE_HOURS = 72.0  # score halves every 3 days


def _score(capture: Capture, now: datetime) -> tuple[float, ScoreBreakdown]:
    priority_score = _PRIORITY_SCORES.get(capture.classification_priority or "", 10.0)
    type_score = _TYPE_SCORES.get(capture.classification_type or "", 5.0)
    confidence_factor = (capture.classification_confidence / 100.0) if capture.classification_confidence is not None else 0.5

    created_at = capture.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = (now - created_at).total_seconds() / 3600.0
    recency_score = round(_RECENCY_MAX * (0.5 ** (age_hours / _RECENCY_HALF_LIFE_HOURS)), 2)

    attention_score = round((priority_score + type_score) * confidence_factor + recency_score, 2)

    breakdown = ScoreBreakdown(
        priority=priority_score,
        capture_type=type_score,
        recency=recency_score,
        confidence_factor=confidence_factor,
    )
    return attention_score, breakdown


def generate_attention_ranking(db: Session) -> AttentionResponse:
    captures = db.query(Capture).filter(Capture.attention_required == True).all()  # noqa: E712
    now = datetime.now(timezone.utc)

    items: list[AttentionItem] = []
    for capture in captures:
        attention_score, breakdown = _score(capture, now)
        items.append(AttentionItem(
            capture=CaptureResponse.model_validate(capture),
            attention_score=attention_score,
            score_breakdown=breakdown,
        ))

    items.sort(key=lambda x: x.attention_score, reverse=True)

    return AttentionResponse(ranked=items, generated_at=now)
