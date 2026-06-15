from pathlib import Path

import yaml

from app.services.roadmap_sync import RoadmapSyncService

_YAML_PATH = Path(__file__).parent.parent.parent.parent / "compass-state.yaml"


async def get_commitments() -> list:
    """Get all active Compass commitments from compass-state.yaml."""
    with open(_YAML_PATH) as f:
        state = yaml.safe_load(f)
    return state.get("commitments", [])


async def sync_roadmap() -> dict:
    """Push the current compass-state.yaml roadmap and commitments to ClickUp.
    Creates missing tasks, updates changed statuses, skips unchanged ones.
    Returns counts of created, updated, and unchanged tasks."""
    svc = RoadmapSyncService()
    result = await svc.sync()
    return {"created": result.created, "updated": result.updated, "unchanged": result.unchanged}
