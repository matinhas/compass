import json
import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

_PROMPT = """Classify the following capture into structured categories. Respond with a JSON object only — no markdown, no explanation.

Capture: {content}

Required JSON fields:
- type: one of Task, Project, Decision, Reference, Alert
- domain: one of Mirra, Personal, Learning, System
- priority: one of Critical, High, Normal, Low
- confidence: integer 0-100 indicating how confident you are in this classification
- reasoning: one sentence explaining the classification
- attention_required: boolean — true if this requires human action or decision (e.g. customer complaint, approval request, supplier decision, accountant request, legal issue, operational risk); false if informational only (e.g. newsletter, promotion, receipt, system notification, marketing email)
- attention_reason: one sentence explaining why attention is required, or null if attention_required is false

Respond with only the JSON object."""


@dataclass
class ClassificationResult:
    type: str
    domain: str
    priority: str
    confidence: int
    reasoning: str
    attention_required: bool
    attention_reason: str | None


class ClassifierService:
    def __init__(self) -> None:
        self._client = AsyncAnthropic()

    async def classify(self, content: str) -> ClassificationResult | None:
        try:
            message = await self._client.messages.create(
                model="claude-opus-4-8",
                max_tokens=256,
                messages=[{"role": "user", "content": _PROMPT.format(content=content)}],
            )
            raw = message.content[0].text.strip()
            data = json.loads(raw)
            return ClassificationResult(
                type=data["type"],
                domain=data["domain"],
                priority=data["priority"],
                confidence=int(data["confidence"]),
                reasoning=data["reasoning"],
                attention_required=bool(data.get("attention_required", False)),
                attention_reason=data.get("attention_reason") or None,
            )
        except Exception as e:
            logger.error("Classification failed: %s: %s", type(e).__name__, e)
            return None
