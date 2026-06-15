from app.database.db import SessionLocal
from app.services.briefing import generate_daily_briefing


def _capture_summary(c) -> dict:
    return {
        "capture_id": c.capture_id,
        "content_preview": c.content[:150],
        "priority": c.classification_priority,
        "type": c.classification_type,
        "domain": c.classification_domain,
        "source_type": c.source_type,
    }


async def get_briefing() -> dict:
    """Get the Compass daily briefing: critical items, high-priority items,
    top 5 ranked captures, and inbox count."""
    db = SessionLocal()
    try:
        b = generate_daily_briefing(db)
        return {
            "critical": [_capture_summary(c) for c in b["critical"]],
            "high": [_capture_summary(c) for c in b["high"]],
            "top5": [_capture_summary(c) for c in b["top5"]],
            "inbox_count": b["inbox_count"],
            "generated_at": b["generated_at"].isoformat(),
        }
    finally:
        db.close()
