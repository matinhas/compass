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
- confidence: integer 0-100
- reasoning: one sentence explaining the classification

Attention detection fields:
- attention_required: boolean — true if this requires human action or decision; false if informational only
  Mark TRUE for: approval/confirmation/authorization requests, customer complaints or disputes, accountant or tax requests, VAT or payroll approvals, overdue payments, contract or legal review, regulatory notices, booking or supplier issues, service interruptions, staff issues
  Mark FALSE for: newsletters, marketing, promotions, receipts, social notifications, automated reports, system alerts without action required
- attention_reason: one short sentence explaining why attention is required, or null if attention_required is false
- attention_category: one of Decision, Customer, Financial, Legal, Operational — or null if attention_required is false
  Decision: approvals, confirmations, authorizations, sign-offs
  Customer: complaints, refunds, escalations, disputes, chargebacks
  Financial: accountant requests, tax questions, VAT, payroll, overdue payments
  Legal: contract review, legal notices, regulatory requests, compliance
  Operational: booking issues, supplier problems, service interruptions, staff issues

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
    attention_category: str | None


class ClassifierService:
    def __init__(self) -> None:
        self._client = AsyncAnthropic()

    async def classify(self, content: str) -> ClassificationResult | None:
        try:
            message = await self._client.messages.create(
                model="claude-opus-4-8",
                max_tokens=512,
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
                attention_category=data.get("attention_category") or None,
            )
        except Exception as e:
            logger.error("Classification failed: %s: %s", type(e).__name__, e)
            return None
