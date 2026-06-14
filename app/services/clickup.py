import os
import httpx

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY", "")
CLICKUP_INBOX_LIST_ID = os.getenv("CLICKUP_INBOX_LIST_ID", "")

CLICKUP_BASE_URL = "https://api.clickup.com/api/v2"


async def create_inbox_task(capture_id: str, content: str) -> str | None:
    if not CLICKUP_API_KEY or not CLICKUP_INBOX_LIST_ID:
        return None

    title = f"[{capture_id}] {content[:120]}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CLICKUP_BASE_URL}/list/{CLICKUP_INBOX_LIST_ID}/task",
            headers={
                "Authorization": CLICKUP_API_KEY,
                "Content-Type": "application/json",
            },
            json={"name": title},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["id"]
