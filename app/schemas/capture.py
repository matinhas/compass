from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class CaptureStatus(str, Enum):
    UNPROCESSED = "UNPROCESSED"
    PROCESSED = "PROCESSED"


class CaptureCreate(BaseModel):
    source: str
    content: str


class CaptureResponse(BaseModel):
    capture_id: str
    source: str
    content: str
    status: CaptureStatus
    created_at: datetime
    clickup_task_id: str | None = None

    classification_type: str | None = None
    classification_domain: str | None = None
    classification_priority: str | None = None
    classification_confidence: int | None = None
    classification_reasoning: str | None = None

    source_type: str | None = None
    source_instance: str | None = None
    external_id: str | None = None

    model_config = {"from_attributes": True}
