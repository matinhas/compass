from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedCapture:
    source_type: str
    source_instance: str
    content: str
    created_at: datetime
    external_id: str | None = None
    metadata: dict = field(default_factory=dict)
