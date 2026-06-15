from sqlalchemy.orm import Session

from app.models.capture import Capture
from app.schemas.capture import CaptureCreate
from app.services.classifier import ClassifierService
from app.services.clickup import create_inbox_task
from app.sources.models import NormalizedCapture

_classifier = ClassifierService()


async def _classify_and_persist(db: Session, capture: Capture) -> None:
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
        pass


async def _clickup_and_persist(db: Session, capture: Capture) -> None:
    try:
        clickup_task_id = await create_inbox_task(capture)
        if clickup_task_id:
            capture.clickup_task_id = clickup_task_id
            db.commit()
            db.refresh(capture)
    except Exception:
        pass


async def create_capture(db: Session, data: CaptureCreate) -> Capture:
    capture = Capture(
        source=data.source,
        content=data.content,
        source_type="manual",
        source_instance="compass",
    )
    db.add(capture)
    db.commit()
    db.refresh(capture)
    await _classify_and_persist(db, capture)
    await _clickup_and_persist(db, capture)
    return capture


async def create_capture_from_source(db: Session, nc: NormalizedCapture) -> Capture | None:
    if nc.external_id:
        existing = db.query(Capture).filter(Capture.external_id == nc.external_id).first()
        if existing:
            return None

    created_at = nc.created_at.replace(tzinfo=None) if nc.created_at.tzinfo else nc.created_at

    capture = Capture(
        source=nc.source_type,
        content=nc.content,
        source_type=nc.source_type,
        source_instance=nc.source_instance,
        external_id=nc.external_id,
        created_at=created_at,
    )
    db.add(capture)
    db.commit()
    db.refresh(capture)
    await _classify_and_persist(db, capture)
    await _clickup_and_persist(db, capture)
    return capture


def list_captures(db: Session) -> list[Capture]:
    return db.query(Capture).order_by(Capture.created_at.desc()).all()
