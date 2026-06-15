from datetime import datetime
from pydantic import BaseModel

from app.schemas.capture import CaptureResponse


class BriefingResponse(BaseModel):
    critical: list[CaptureResponse]
    high: list[CaptureResponse]
    top5: list[CaptureResponse]
    inbox_count: int
    generated_at: datetime
