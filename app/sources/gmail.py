import os
from datetime import datetime, timezone

import httpx

from app.sources.base import SourceProvider
from app.sources.models import NormalizedCapture

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailSource(SourceProvider):
    def __init__(self, account: str) -> None:
        self._account = account
        self._client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self._client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self._refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "")

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def fetch(self) -> list[NormalizedCapture]:
        if not all([self._client_id, self._client_secret, self._refresh_token]):
            raise ValueError("Gmail credentials not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            token = await self._get_access_token(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.get(
                f"{_GMAIL_BASE}/messages",
                headers=headers,
                params={"q": "is:unread newer_than:7d", "maxResults": 100},
            )
            resp.raise_for_status()
            messages = resp.json().get("messages", [])

            captures: list[NormalizedCapture] = []
            for msg in messages:
                detail = await client.get(
                    f"{_GMAIL_BASE}/messages/{msg['id']}",
                    headers=headers,
                    params={
                        "format": "metadata",
                        "metadataHeaders": ["Subject", "From"],
                    },
                )
                detail.raise_for_status()
                data = detail.json()

                msg_headers = data.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in msg_headers if h["name"] == "Subject"), "(no subject)")
                sender = next((h["value"] for h in msg_headers if h["name"] == "From"), "(unknown)")
                snippet = data.get("snippet", "")

                content = f"Subject: {subject}\n\nFrom: {sender}\n\nSnippet:\n{snippet}"
                email_ts = datetime.fromtimestamp(int(data["internalDate"]) / 1000, tz=timezone.utc)

                captures.append(NormalizedCapture(
                    source_type="gmail",
                    source_instance=self._account,
                    external_id=msg["id"],
                    content=content,
                    created_at=email_ts,
                    metadata={"subject": subject, "from": sender},
                ))

            return captures
