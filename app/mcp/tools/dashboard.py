from app.database.db import SessionLocal
from app.services.dashboard import generate_dashboard


async def get_dashboard() -> dict:
    """Get the Compass executive dashboard: critical/high counts, captures today,
    source breakdown, domain breakdown, and top 5 attention items."""
    db = SessionLocal()
    try:
        return generate_dashboard(db).model_dump()
    finally:
        db.close()
