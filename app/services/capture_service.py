from sqlalchemy.orm import Session

from app.models.capture import Capture
from app.schemas.capture import CaptureCreate
from app.services.clickup import create_inbox_task


async def create_capture(db: Session, data: CaptureCreate) -> Capture:
    capture = Capture(source=data.source, content=data.content)
    db.add(capture)
    db.commit()
    db.refresh(capture)

    try:
        clickup_task_id = await create_inbox_task(capture.capture_id, capture.content)
        if clickup_task_id:
            capture.clickup_task_id = clickup_task_id
            db.commit()
            db.refresh(capture)
    except Exception:
        pass  # ClickUp failure must not block capture creation

    return capture


def list_captures(db: Session) -> list[Capture]:
    return db.query(Capture).order_by(Capture.created_at.desc()).all()
