from app.database.db import SessionLocal
from app.services.attention import generate_attention_ranking


async def get_attention() -> dict:
    """Get the top 10 Compass attention items ranked by priority, type,
    recency, and classification confidence."""
    db = SessionLocal()
    try:
        result = generate_attention_ranking(db)
        top = result.ranked[:10]
        return {
            "ranked": [
                {
                    "capture_id": item.capture.capture_id,
                    "content_preview": item.capture.content[:150],
                    "attention_score": item.attention_score,
                    "priority": item.capture.classification_priority,
                    "type": item.capture.classification_type,
                    "domain": item.capture.classification_domain,
                    "source_type": item.capture.source_type,
                    "score_breakdown": item.score_breakdown.model_dump(),
                }
                for item in top
            ],
            "generated_at": result.generated_at.isoformat(),
        }
    finally:
        db.close()
