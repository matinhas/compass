import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum

from app.database.db import Base


class CaptureStatus(str, enum.Enum):
    UNPROCESSED = "UNPROCESSED"
    PROCESSED = "PROCESSED"


class Capture(Base):
    __tablename__ = "captures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(CaptureStatus), nullable=False, default=CaptureStatus.UNPROCESSED)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    clickup_task_id = Column(String, nullable=True)

    @property
    def capture_id(self) -> str:
        return f"CAP-{self.id:05d}"
