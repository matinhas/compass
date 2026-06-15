import os
import re
from pathlib import Path
from typing import NamedTuple

import httpx
import yaml

_CLICKUP_BASE = "https://api.clickup.com/api/v2"
_YAML_PATH = Path(__file__).parent.parent.parent / "compass-state.yaml"

_STATUS_MAP = {
    "planned": "to do",
    "active": "in progress",
    "complete": "complete",
}

# Matches the [KEY] prefix at the start of a task name, e.g. "[MVP-005.1]" or "[CMP-002]"
_KEY_RE = re.compile(r"^\[([^\]]+)\]")


def _extract_key(task_name: str) -> str | None:
    m = _KEY_RE.match(task_name)
    return m.group(1) if m else None


class SyncResult(NamedTuple):
    created: int
    updated: int
    unchanged: int


class RoadmapSyncService:
    def __init__(self) -> None:
        self._api_key = os.getenv("CLICKUP_API_KEY", "")
        self._roadmap_list_id = os.getenv("CLICKUP_ROADMAP_LIST_ID", "")
        self._commitments_list_id = os.getenv("CLICKUP_COMMITMENTS_LIST_ID", "")

    def _load_state(self) -> dict:
        with open(_YAML_PATH) as f:
            return yaml.safe_load(f)

    def _build_roadmap_tasks(self, state: dict) -> dict[str, tuple[str, str]]:
        """Returns {key: (full_name, clickup_status)}."""
        tasks: dict[str, tuple[str, str]] = {}
        for key, entry in state.get("roadmap", {}).items():
            name = f"[{key}] {entry['name']}"
            status = _STATUS_MAP.get(entry.get("status", "planned"), "to do")
            tasks[key] = (name, status)
        return tasks

    def _build_commitment_tasks(self, state: dict) -> dict[str, tuple[str, str]]:
        """Returns {key: (full_name, clickup_status)}."""
        tasks: dict[str, tuple[str, str]] = {}
        for c in state.get("commitments", []):
            name = f"[{c['id']}] {c['title']}"
            status = _STATUS_MAP.get(c.get("status", "planned"), "to do")
            tasks[c["id"]] = (name, status)
        return tasks

    async def _fetch_list_tasks(
        self, client: httpx.AsyncClient, list_id: str
    ) -> dict[str, tuple[str, str, str]]:
        """Returns {key: (task_id, task_name, current_status_lowercase)}.

        Key is extracted from the [KEY] prefix of the task name. Tasks without
        a recognisable prefix are skipped (not managed by Compass).
        """
        headers = {"Authorization": self._api_key}
        result: dict[str, tuple[str, str, str]] = {}
        page = 0
        while True:
            resp = await client.get(
                f"{_CLICKUP_BASE}/list/{list_id}/task",
                headers=headers,
                params={"include_closed": "true", "page": page},
            )
            resp.raise_for_status()
            body = resp.json()
            for task in body.get("tasks", []):
                key = _extract_key(task["name"])
                if key:
                    current = task["status"]["status"].lower()
                    result[key] = (task["id"], task["name"], current)
            if body.get("last_page"):
                break
            page += 1
        return result

    async def _create_task(
        self, client: httpx.AsyncClient, list_id: str, name: str, status: str
    ) -> None:
        resp = await client.post(
            f"{_CLICKUP_BASE}/list/{list_id}/task",
            headers={"Authorization": self._api_key, "Content-Type": "application/json"},
            json={"name": name, "status": status},
            timeout=10.0,
        )
        resp.raise_for_status()

    async def _update_task(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        name: str | None = None,
        status: str | None = None,
    ) -> None:
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if status is not None:
            payload["status"] = status
        resp = await client.put(
            f"{_CLICKUP_BASE}/task/{task_id}",
            headers={"Authorization": self._api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()

    async def _sync_list(
        self,
        client: httpx.AsyncClient,
        list_id: str,
        expected: dict[str, tuple[str, str]],
    ) -> SyncResult:
        existing = await self._fetch_list_tasks(client, list_id)
        created = updated = unchanged = 0

        for key, (target_name, target_status) in expected.items():
            if key not in existing:
                await self._create_task(client, list_id, target_name, target_status)
                created += 1
            else:
                task_id, current_name, current_status = existing[key]
                name_drift = current_name != target_name
                status_drift = current_status != target_status
                if name_drift or status_drift:
                    await self._update_task(
                        client,
                        task_id,
                        name=target_name if name_drift else None,
                        status=target_status if status_drift else None,
                    )
                    updated += 1
                else:
                    unchanged += 1

        return SyncResult(created=created, updated=updated, unchanged=unchanged)

    async def sync(self) -> SyncResult:
        if not self._api_key:
            raise ValueError("CLICKUP_API_KEY not configured.")
        if not self._roadmap_list_id:
            raise ValueError("CLICKUP_ROADMAP_LIST_ID not configured.")

        state = self._load_state()

        async with httpx.AsyncClient(timeout=15.0) as client:
            result = await self._sync_list(
                client, self._roadmap_list_id, self._build_roadmap_tasks(state)
            )

            if self._commitments_list_id and state.get("commitments"):
                c = await self._sync_list(
                    client, self._commitments_list_id, self._build_commitment_tasks(state)
                )
                result = SyncResult(
                    created=result.created + c.created,
                    updated=result.updated + c.updated,
                    unchanged=result.unchanged + c.unchanged,
                )

        return result
