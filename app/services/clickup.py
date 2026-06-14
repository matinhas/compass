import os
import httpx

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY", "")
CLICKUP_INBOX_LIST_ID = os.getenv("CLICKUP_INBOX_LIST_ID", "")

CLICKUP_BASE_URL = "https://api.clickup.com/api/v2"


async def create_inbox_task(capture) -> str | None:
    if not CLICKUP_API_KEY or not CLICKUP_INBOX_LIST_ID:
        return None

    title = f"[{capture.capture_id}] {capture.content[:120]}"

    description_lines = []
    if capture.classification_type:
        description_lines.append(
            f"Classification: {capture.classification_type} | "
            f"{capture.classification_domain} | "
            f"{capture.classification_priority} | "
            f"Confidence: {capture.classification_confidence}%"
        )
        if capture.classification_reasoning:
            description_lines.append(f"Reasoning: {capture.classification_reasoning}")

    description = "\n".join(description_lines) if description_lines else None

    payload: dict = {"name": title}
    if description:
        payload["description"] = description

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CLICKUP_BASE_URL}/list/{CLICKUP_INBOX_LIST_ID}/task",
            headers={
                "Authorization": CLICKUP_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["id"]
