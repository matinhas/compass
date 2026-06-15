from pathlib import Path

import yaml

_YAML_PATH = Path(__file__).parent.parent.parent.parent / "compass-state.yaml"


async def get_roadmap() -> dict:
    """Get the current Compass roadmap from compass-state.yaml.
    Returns each milestone key with its name and status (planned/active/complete)."""
    with open(_YAML_PATH) as f:
        state = yaml.safe_load(f)
    return {
        key: {"name": entry["name"], "status": entry["status"]}
        for key, entry in state.get("roadmap", {}).items()
    }
