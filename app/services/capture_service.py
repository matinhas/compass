from sqlalchemy.orm import Session

from app.models.capture import Capture
from app.schemas.capture import CaptureCreate
from app.services.classifier import ClassifierService
from app.services.clickup import create_inbox_task

_classifier = ClassifierService()


async def create_capture(db: Session, data: CaptureCreate) -> Capture:
    capture = Capture(source=data.source, content=data.content)
    db.add(capture)
    db.commit()
    db.refresh(capture)

    try:
        result = await _classifier.classify(capture.content)
        if result:
            capture.classification_type = result.type
            capture.classification_domain = result.domain
            capture.classification_priority = result.priority
            capture.classification_confidence = result.confidence
            capture.classification_reasoning = result.reasoning
            db.commit()
            db.refresh(capture)
    except Exception:
        pass  # Classification failure must not block capture creation

    try:
        clickup_task_id = await create_inbox_task(capture)
        if clickup_task_id:
            capture.clickup_task_id = clickup_task_id
            db.commit()
            db.refresh(capture)
    except Exception:
        pass  # ClickUp failure must not block capture creation

    return capture


def list_captures(db: Session) -> list[Capture]:
    return db.query(Capture).order_by(Capture.created_at.desc()).all()
