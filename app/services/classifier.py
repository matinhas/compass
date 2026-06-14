import json
import os
from dataclasses import dataclass

from anthropic import AsyncAnthropic

_PROMPT = """Classify the following capture into structured categories. Respond with a JSON object only — no markdown, no explanation.

Capture: {content}

Required JSON fields:
- type: one of Task, Project, Decision, Reference, Alert
- domain: one of Mirra, Personal, Learning, System
- priority: one of Critical, High, Normal, Low
- confidence: integer 0-100 indicating how confident you are in this classification
- reasoning: one sentence explaining the classification

Respond with only the JSON object."""


@dataclass
class ClassificationResult:
    type: str
    domain: str
    priority: str
    confidence: int
    reasoning: str


class ClassifierService:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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
            )
        except Exception:
            return None
