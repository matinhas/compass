import os
import re
from datetime import datetime, timezone
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

    def _get_current_focus_name(self, state: dict) -> str:
        """Return the display name of the current focus item."""
        focus_items = state.get("current_focus", [])
        if not focus_items:
            return ""
        item = focus_items[-1]
        if isinstance(item, dict):
            return next(iter(item.values()), "")
        return str(item)

    def _build_status_description(self, state: dict) -> str:
        """Generate the [STATUS] task description from current roadmap state."""
        roadmap = state.get("roadmap", {})

        layers: dict[str, list[str]] = {
            "Foundation Layer": ["MVP-001", "MVP-002", "MVP-003", "MVP-004"],
            "Integrations": sorted(k for k in roadmap if k.startswith("MVP-005")),
            "Operations Layer": sorted(k for k in roadmap if k.startswith("MVP-006")),
        }

        lines: list[str] = []
        for layer_name, keys in layers.items():
            statuses = [roadmap[k]["status"] for k in keys if k in roadmap]
            if not statuses:
                continue
            complete_count = sum(1 for s in statuses if s == "complete")
            if complete_count == len(statuses):
                lines.append(f"{layer_name}\n✅ Complete")
            else:
                pct = int(complete_count / len(statuses) * 100)
                lines.append(f"{layer_name}\n{pct}%")

        focus_name = self._get_current_focus_name(state)
        if focus_name:
            lines.append(f"Current Focus:\n{focus_name}")

        next_name = next(
            (entry["name"] for entry in roadmap.values() if entry.get("status") == "planned"),
            None,
        )
        if next_name:
            lines.append(f"Next:\n{next_name}")

        return "\n\n".join(lines)

    async def _fetch_list_tasks(
        self, client: httpx.AsyncClient, list_id: str
    ) -> dict[str, tuple[str, str, str]]:
        """Returns {key: (task_id, task_name, current_status_lowercase)}.

        Tasks without a recognisable [KEY] prefix are skipped.
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
        self,
        client: httpx.AsyncClient,
        list_id: str,
        name: str,
        status: str,
        description: str | None = None,
    ) -> str:
        payload: dict = {"name": name, "status": status}
        if description is not None:
            payload["description"] = description
        resp = await client.post(
            f"{_CLICKUP_BASE}/list/{list_id}/task",
            headers={"Authorization": self._api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    async def _update_task(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        name: str | None = None,
        status: str | None = None,
        description: str | None = None,
    ) -> None:
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if status is not None:
            payload["status"] = status
        if description is not None:
            payload["description"] = description
        if not payload:
            return
        resp = await client.put(
            f"{_CLICKUP_BASE}/task/{task_id}",
            headers={"Authorization": self._api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()

    async def _add_comment(
        self, client: httpx.AsyncClient, task_id: str, comment: str
    ) -> None:
        resp = await client.post(
            f"{_CLICKUP_BASE}/task/{task_id}/comment",
            headers={"Authorization": self._api_key, "Content-Type": "application/json"},
            json={"comment_text": comment},
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
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

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
                    if status_drift and target_status == "complete" and current_status != "complete":
                        comment = f"Milestone completed by Compass Sync.\n\nDate: {today}"
                        await self._add_comment(client, task_id, comment)
                    updated += 1
                else:
                    unchanged += 1

        return SyncResult(created=created, updated=updated, unchanged=unchanged)

    async def sync_focus(
        self, client: httpx.AsyncClient, state: dict
    ) -> SyncResult:
        """Maintain exactly one [FOCUS] task in the roadmap list."""
        focus_name = self._get_current_focus_name(state)
        if not focus_name:
            return SyncResult(created=0, updated=0, unchanged=0)

        target_name = f"[FOCUS] {focus_name}"
        target_status = "in progress"

        existing = await self._fetch_list_tasks(client, self._roadmap_list_id)

        if "FOCUS" not in existing:
            await self._create_task(client, self._roadmap_list_id, target_name, target_status)
            return SyncResult(created=1, updated=0, unchanged=0)

        task_id, current_name, current_status = existing["FOCUS"]
        name_drift = current_name != target_name
        status_drift = current_status != target_status
        if name_drift or status_drift:
            await self._update_task(
                client,
                task_id,
                name=target_name if name_drift else None,
                status=target_status if status_drift else None,
            )
            return SyncResult(created=0, updated=1, unchanged=0)

        return SyncResult(created=0, updated=0, unchanged=1)

    async def sync_status_summary(
        self, client: httpx.AsyncClient, state: dict
    ) -> SyncResult:
        """Maintain the [STATUS] Compass Project Status task with live description."""
        target_name = "[STATUS] Compass Project Status"
        target_status = "in progress"
        description = self._build_status_description(state)

        existing = await self._fetch_list_tasks(client, self._roadmap_list_id)

        if "STATUS" not in existing:
            await self._create_task(
                client, self._roadmap_list_id, target_name, target_status, description
            )
            return SyncResult(created=1, updated=0, unchanged=0)

        task_id, current_name, current_status = existing["STATUS"]
        name_drift = current_name != target_name
        status_drift = current_status != target_status
        await self._update_task(
            client,
            task_id,
            name=target_name if name_drift else None,
            status=target_status if status_drift else None,
            description=description,
        )
        return SyncResult(created=0, updated=1, unchanged=0)

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

            f = await self.sync_focus(client, state)
            result = SyncResult(
                created=result.created + f.created,
                updated=result.updated + f.updated,
                unchanged=result.unchanged + f.unchanged,
            )

            s = await self.sync_status_summary(client, state)
            result = SyncResult(
                created=result.created + s.created,
                updated=result.updated + s.updated,
                unchanged=result.unchanged + s.unchanged,
            )

        return result
