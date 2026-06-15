import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.models.capture import Capture
from app.schemas.dashboard import DashboardResponse, DashboardTopItem
from app.services.attention import _score

_YAML_PATH = Path(__file__).parent.parent.parent / "compass-state.yaml"


def _load_compass_state() -> dict:
    with open(_YAML_PATH) as f:
        return yaml.safe_load(f)


def _compass_focus(state: dict) -> str:
    items = state.get("current_focus", [])
    if not items:
        return ""
    item = items[-1]
    if isinstance(item, dict):
        return next(iter(item.values()), "")
    return str(item)


def generate_dashboard(db: Session) -> DashboardResponse:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    captures = db.query(Capture).all()

    critical_count = 0
    high_count = 0
    captures_today = 0
    source_breakdown: dict[str, int] = defaultdict(int)
    domain_breakdown: dict[str, int] = defaultdict(int)
    scored: list[tuple[float, Capture]] = []

    for c in captures:
        if c.classification_priority == "Critical":
            critical_count += 1
        elif c.classification_priority == "High":
            high_count += 1

        if c.created_at >= today_start:
            captures_today += 1

        source_breakdown[c.source_type or c.source or "manual"] += 1

        if c.classification_domain:
            domain_breakdown[c.classification_domain] += 1

        score, _ = _score(c, now)
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)

    top_attention = [
        DashboardTopItem(
            capture_id=c.capture_id,
            content_preview=c.content[:120],
            priority=c.classification_priority,
            source_type=c.source_type,
            attention_score=score,
        )
        for score, c in scored[:5]
    ]

    state = _load_compass_state()
    roadmap = state.get("roadmap", {})
    commitments = state.get("commitments", [])

    total = len(roadmap)
    complete_count = sum(1 for e in roadmap.values() if e.get("status") == "complete")
    roadmap_progress = int(complete_count / total * 100) if total else 0

    from app.services.system_status import check_system_health
    status_data = asyncio.run(check_system_health())
    system_health = status_data["overall"]

    return DashboardResponse(
        critical_count=critical_count,
        high_count=high_count,
        captures_today=captures_today,
        source_breakdown=dict(source_breakdown),
        domain_breakdown=dict(domain_breakdown),
        top_attention=top_attention,
        generated_at=now.isoformat(),
        current_focus=_compass_focus(state),
        active_commitments=sum(1 for c in commitments if c.get("status") == "active"),
        completed_milestones=complete_count,
        roadmap_progress=roadmap_progress,
        system_health=system_health,
    )
