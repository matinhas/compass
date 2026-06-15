from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.capture import Capture
from app.services.attention import _score


def generate_daily_briefing(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    gmail_today = db.query(Capture).filter(
        Capture.source_type == "gmail",
        Capture.created_at >= today_start,
    ).all()

    emails_received_today = len(gmail_today)
    require_attention = sum(1 for c in gmail_today if c.attention_required)

    attention_captures = db.query(Capture).filter(
        Capture.attention_required == True,  # noqa: E712
    ).all()

    scored = sorted(
        [(s, c) for c in attention_captures for s, _ in [_score(c, now)]],
        key=lambda x: x[0],
        reverse=True,
    )

    top_attention = [
        {
            "capture_id": f"CAP-{c.id:05d}",
            "source": c.source_type or c.source or "manual",
            "priority": c.classification_priority,
            "category": c.attention_category,
            "reason": c.attention_reason,
            "preview": c.content[:120],
            "attention_score": score,
        }
        for score, c in scored[:5]
    ]

    critical_count = sum(1 for _, c in scored if c.classification_priority == "Critical")
    high_count = sum(1 for _, c in scored if c.classification_priority == "High")

    return {
        "emails_received_today": emails_received_today,
        "require_attention": require_attention,
        "critical_count": critical_count,
        "high_count": high_count,
        "top_attention": top_attention,
        "generated_at": now,
    }
