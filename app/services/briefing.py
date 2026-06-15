from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.capture import Capture, CaptureStatus


def generate_daily_briefing(db: Session) -> dict:
    all_captures = (
        db.query(Capture)
        .order_by(Capture.created_at.desc())
        .all()
    )

    critical = [c for c in all_captures if c.classification_priority == "Critical"]
    high = [c for c in all_captures if c.classification_priority == "High"]

    ranked = critical + high + [
        c for c in all_captures
        if c.classification_priority not in ("Critical", "High")
    ]
    top5 = ranked[:5]

    inbox_count = sum(1 for c in all_captures if c.status == CaptureStatus.UNPROCESSED)

    return {
        "critical": critical,
        "high": high,
        "top5": top5,
        "inbox_count": inbox_count,
        "generated_at": datetime.now(timezone.utc),
    }
