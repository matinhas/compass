import os
from datetime import datetime, timedelta, timezone

import httpx

from app.sources.base import SourceProvider
from app.sources.models import NormalizedCapture

_BASE = "https://api.respond.io/v2"

_CUSTOMER_RISK_LABELS = {"escalated", "complaint", "unhappy", "refund", "cancellation", "dispute", "chargeback"}
_STAFF_RISK_LABELS = {"staff-issue", "staff-complaint", "misconduct", "hr", "conduct"}
_OPERATIONAL_RISK_LABELS = {"urgent", "critical", "outage", "system-error", "bug", "data-loss", "blocked"}

_CSAT_RISK_THRESHOLD = 3       # score ≤ this → customer_risk
_UNRESOLVED_RISK_DAYS = 3      # open for ≥ this many days → operational_risk
_LOOKBACK_DAYS = 7


def _detect_risk(conv: dict) -> str | None:
    labels = {str(l).lower() for l in conv.get("labels", [])}

    csat = conv.get("csatScore")
    if csat is not None and csat <= _CSAT_RISK_THRESHOLD:
        return "customer_risk"

    if labels & _CUSTOMER_RISK_LABELS:
        return "customer_risk"
    if labels & _STAFF_RISK_LABELS:
        return "staff_risk"
    if labels & _OPERATIONAL_RISK_LABELS:
        return "operational_risk"

    if conv.get("status") == "open":
        raw = conv.get("createdAt", "")
        try:
            created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created).days
            if age_days >= _UNRESOLVED_RISK_DAYS:
                return "operational_risk"
        except (ValueError, AttributeError):
            pass

    return None


def _build_capture(conv: dict, risk_type: str, instance: str) -> NormalizedCapture:
    contact = conv.get("contact", {})
    contact_name = contact.get("name") or contact.get("phoneNumber") or contact.get("email") or "Unknown"
    labels = conv.get("labels", [])
    status = conv.get("status", "unknown")
    last_message = (conv.get("lastMessage") or {}).get("text") or ""

    content = (
        f"Risk Type: {risk_type.replace('_', ' ').title()}\n\n"
        f"Contact: {contact_name}\n\n"
        f"Status: {status}\n\n"
        f"Labels: {', '.join(str(l) for l in labels) if labels else 'none'}\n\n"
        f"Last Message:\n{last_message}"
    )

    raw_ts = conv.get("createdAt", "")
    try:
        created_at = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        created_at = datetime.now(timezone.utc)

    return NormalizedCapture(
        source_type="respondio",
        source_instance=instance,
        external_id=f"respondio_{conv['id']}",
        content=content,
        created_at=created_at,
        metadata={
            "risk_type": risk_type,
            "contact_name": contact_name,
            "labels": labels,
            "status": status,
            "conversation_id": conv["id"],
        },
    )


class RespondIoSource(SourceProvider):
    def __init__(self, instance: str = "mirra") -> None:
        self._instance = instance
        self._api_key = os.getenv("RESPONDIO_API_KEY", "")
        self.conversations_scanned: int = 0

    async def _list_conversations(self, client: httpx.AsyncClient) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        cutoff = (datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)).isoformat()

        conversations: list[dict] = []
        cursor: str | None = None

        while True:
            params: dict = {"limit": 100, "sortBy": "updatedAt", "sortOrder": "desc"}
            if cursor:
                params["cursor"] = cursor

            resp = await client.get(f"{_BASE}/conversation/", headers=headers, params=params)
            resp.raise_for_status()
            body = resp.json()

            items = body.get("data", {}).get("items", [])
            for item in items:
                updated = item.get("updatedAt", "")
                try:
                    updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    if updated_dt < datetime.fromisoformat(cutoff):
                        return conversations  # sorted desc, safe to stop
                except (ValueError, AttributeError):
                    pass
                conversations.append(item)

            cursor = body.get("data", {}).get("pagingMeta", {}).get("nextCursor")
            if not cursor:
                break

        return conversations

    async def fetch(self) -> list[NormalizedCapture]:
        if not self._api_key:
            raise ValueError("RESPONDIO_API_KEY not configured.")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            conversations = await self._list_conversations(client)

        self.conversations_scanned = len(conversations)

        captures: list[NormalizedCapture] = []
        for conv in conversations:
            risk_type = _detect_risk(conv)
            if risk_type:
                captures.append(_build_capture(conv, risk_type, self._instance))

        return captures
