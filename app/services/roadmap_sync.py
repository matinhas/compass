import os
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

    def _build_roadmap_tasks(self, state: dict) -> dict[str, str]:
        tasks: dict[str, str] = {}
        for key, entry in state.get("roadmap", {}).items():
            name = f"[{key}] {entry['name']}"
            tasks[name] = _STATUS_MAP.get(entry.get("status", "planned"), "to do")
        return tasks

    def _build_commitment_tasks(self, state: dict) -> dict[str, str]:
        tasks: dict[str, str] = {}
        for c in state.get("commitments", []):
            name = f"[{c['id']}] {c['title']}"
            tasks[name] = _STATUS_MAP.get(c.get("status", "planned"), "to do")
        return tasks

    async def _fetch_list_tasks(
        self, client: httpx.AsyncClient, list_id: str
    ) -> dict[str, tuple[str, str]]:
        """Returns {task_name: (task_id, current_status_lowercase)}."""
        headers = {"Authorization": self._api_key}
        result: dict[str, tuple[str, str]] = {}
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
                current = task["status"]["status"].lower()
                result[task["name"]] = (task["id"], current)
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

    async def _update_task_status(
        self, client: httpx.AsyncClient, task_id: str, status: str
    ) -> None:
        resp = await client.put(
            f"{_CLICKUP_BASE}/task/{task_id}",
            headers={"Authorization": self._api_key, "Content-Type": "application/json"},
            json={"status": status},
            timeout=10.0,
        )
        resp.raise_for_status()

    async def _sync_list(
        self,
        client: httpx.AsyncClient,
        list_id: str,
        expected: dict[str, str],
    ) -> SyncResult:
        existing = await self._fetch_list_tasks(client, list_id)
        created = updated = unchanged = 0

        for name, target_status in expected.items():
            if name not in existing:
                await self._create_task(client, list_id, name, target_status)
                created += 1
            else:
                task_id, current_status = existing[name]
                if current_status != target_status:
                    await self._update_task_status(client, task_id, target_status)
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
