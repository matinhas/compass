import os
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx

from app.sources.base import SourceProvider
from app.sources.models import NormalizedCapture

_BASE = "https://api.respond.io/v2"

_CUSTOMER_RISK_LABELS = {"escalated", "complaint", "unhappy", "refund", "cancellation", "dispute", "chargeback"}
_STAFF_RISK_LABELS = {"staff-issue", "staff-complaint", "misconduct", "hr", "conduct"}
_OPERATIONAL_RISK_LABELS = {"urgent", "critical", "outage", "system-error", "bug", "data-loss", "blocked"}

_UNRESOLVED_RISK_DAYS = 3
_LOOKBACK_DAYS = 7


def _detect_risk(contact: dict) -> str | None:
    tags = {str(t).lower() for t in contact.get("tags", [])}

    if tags & _CUSTOMER_RISK_LABELS:
        return "customer_risk"
    if tags & _STAFF_RISK_LABELS:
        return "staff_risk"
    if tags & _OPERATIONAL_RISK_LABELS:
        return "operational_risk"

    if contact.get("status") == "open":
        created_ts = contact.get("created_at", 0)
        age_days = (datetime.now(timezone.utc).timestamp() - created_ts) / 86400
        if age_days >= _UNRESOLVED_RISK_DAYS:
            return "operational_risk"

    return None


def _build_capture(contact: dict, risk_type: str, instance: str) -> NormalizedCapture:
    first = contact.get("firstName") or ""
    last = contact.get("lastName") or ""
    contact_name = f"{first} {last}".strip() or contact.get("phone") or contact.get("email") or "Unknown"
    tags = contact.get("tags", [])
    status = contact.get("status", "unknown")
    lifecycle = contact.get("lifecycle") or ""

    content = (
        f"Risk Type: {risk_type.replace('_', ' ').title()}\n\n"
        f"Contact: {contact_name}\n\n"
        f"Status: {status}\n\n"
        f"Lifecycle: {lifecycle}\n\n"
        f"Labels: {', '.join(str(t) for t in tags) if tags else 'none'}"
    )

    created_ts = contact.get("created_at", 0)
    created_at = datetime.fromtimestamp(created_ts, tz=timezone.utc) if created_ts else datetime.now(timezone.utc)

    return NormalizedCapture(
        source_type="respondio",
        source_instance=instance,
        external_id=f"respondio_{contact['id']}",
        content=content,
        created_at=created_at,
        metadata={
            "risk_type": risk_type,
            "contact_name": contact_name,
            "tags": tags,
            "status": status,
            "conversation_id": contact["id"],
        },
    )


class RespondIoSource(SourceProvider):
    def __init__(self, instance: str = "mirra") -> None:
        self._instance = instance
        self._api_key = os.getenv("RESPONDIO_API_KEY", "")
        self.conversations_scanned: int = 0

    async def _list_contacts(self, client: httpx.AsyncClient) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)).timestamp()

        contacts: list[dict] = []
        cursor: int | None = None

        while True:
            params: dict = {"limit": 100}
            if cursor:
                params["cursorId"] = cursor

            resp = await client.get(f"{_BASE}/contact/list", headers=headers, params=params)
            resp.raise_for_status()
            body = resp.json()

            items = body.get("items", [])
            for item in items:
                created_ts = item.get("created_at", 0)
                if created_ts < cutoff_ts:
                    return contacts  # items sorted by id desc (≈ newest first), safe to stop
                contacts.append(item)

            next_url = body.get("pagination", {}).get("next")
            if not next_url:
                break

            parsed = urllib.parse.urlparse(next_url)
            qs = urllib.parse.parse_qs(parsed.query)
            cursor_list = qs.get("cursorId", [])
            if not cursor_list:
                break
            cursor = int(cursor_list[0])

        return contacts

    async def fetch(self) -> list[NormalizedCapture]:
        if not self._api_key:
            raise ValueError("RESPONDIO_API_KEY not configured.")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            contacts = await self._list_contacts(client)

        self.conversations_scanned = len(contacts)

        captures: list[NormalizedCapture] = []
        for contact in contacts:
            risk_type = _detect_risk(contact)
            if risk_type:
                captures.append(_build_capture(contact, risk_type, self._instance))

        return captures
