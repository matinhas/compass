import os

from sqlalchemy import text

from app.database.db import SessionLocal


async def check_system_health() -> dict:
    """Check health of all Compass subsystems. Returns per-service status and overall."""
    environment = "production" if os.getenv("RAILWAY_ENVIRONMENT") else "local"

    db_status = "healthy"
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        db_status = "unhealthy"

    roadmap_status = (
        "healthy"
        if os.getenv("CLICKUP_API_KEY") and os.getenv("CLICKUP_ROADMAP_LIST_ID")
        else "unconfigured"
    )

    gmail_status = (
        "healthy"
        if (
            os.getenv("GOOGLE_CLIENT_ID")
            and os.getenv("GOOGLE_CLIENT_SECRET")
            and any(k.startswith("GOOGLE_REFRESH_TOKEN_") for k in os.environ)
        )
        else "unconfigured"
    )

    respondio_status = "healthy" if os.getenv("RESPONDIO_API_KEY") else "unconfigured"

    overall = (
        "healthy"
        if all(s == "healthy" for s in [db_status, roadmap_status, gmail_status, respondio_status])
        else "degraded"
    )

    return {
        "environment": environment,
        "overall": overall,
        "database": db_status,
        "roadmap_sync": roadmap_status,
        "gmail": gmail_status,
        "respondio": respondio_status,
        "version": "0.1.0",
    }
