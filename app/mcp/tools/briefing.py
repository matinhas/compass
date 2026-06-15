from app.database.db import SessionLocal
from app.services.briefing import generate_daily_briefing


async def get_briefing() -> dict:
    """Get the Compass daily briefing: email volume, attention counts, and top attention items."""
    db = SessionLocal()
    try:
        b = generate_daily_briefing(db)
        return {
            "emails_received_today": b["emails_received_today"],
            "require_attention": b["require_attention"],
            "critical_count": b["critical_count"],
            "high_count": b["high_count"],
            "top_attention": b["top_attention"],
            "generated_at": b["generated_at"].isoformat(),
        }
    finally:
        db.close()
