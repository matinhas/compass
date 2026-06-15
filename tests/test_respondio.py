import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.sources.respondio import RespondIoSource, _detect_risk, _build_capture


def _conv(
    id: int = 1,
    status: str = "open",
    labels: list = None,
    csat: int | None = None,
    created_days_ago: int = 1,
) -> dict:
    created = (datetime.now(timezone.utc) - timedelta(days=created_days_ago)).isoformat()
    return {
        "id": id,
        "status": status,
        "labels": labels or [],
        "csatScore": csat,
        "createdAt": created,
        "updatedAt": created,
        "contact": {"name": "Test Contact", "phoneNumber": "+351910000000"},
        "lastMessage": {"text": "Last message text"},
    }


def test_low_csat_creates_customer_risk():
    conv = _conv(csat=2)
    assert _detect_risk(conv) == "customer_risk"


def test_csat_above_threshold_not_risk():
    conv = _conv(csat=4)
    assert _detect_risk(conv) is None


def test_customer_risk_label():
    conv = _conv(labels=["escalated"])
    assert _detect_risk(conv) == "customer_risk"


def test_staff_risk_label():
    conv = _conv(labels=["misconduct"])
    assert _detect_risk(conv) == "staff_risk"


def test_operational_risk_label():
    conv = _conv(labels=["outage"])
    assert _detect_risk(conv) == "operational_risk"


def test_unresolved_3_days_is_operational_risk():
    conv = _conv(status="open", created_days_ago=4)
    assert _detect_risk(conv) == "operational_risk"


def test_unresolved_1_day_not_risk():
    conv = _conv(status="open", created_days_ago=1)
    assert _detect_risk(conv) is None


def test_resolved_old_conversation_not_risk():
    conv = _conv(status="resolved", created_days_ago=10)
    assert _detect_risk(conv) is None


def test_no_risk_conversation_skipped():
    conv = _conv(labels=[], csat=None, status="open", created_days_ago=1)
    assert _detect_risk(conv) is None


def test_build_capture_sets_correct_fields():
    conv = _conv(id=42, labels=["escalated"], csat=2)
    nc = _build_capture(conv, "customer_risk", "mirra")

    assert nc.source_type == "respondio"
    assert nc.source_instance == "mirra"
    assert nc.external_id == "respondio_42"
    assert nc.metadata["risk_type"] == "customer_risk"
    assert nc.metadata["conversation_id"] == 42
    assert "Customer Risk" in nc.content
    assert "Test Contact" in nc.content


async def test_fetch_filters_only_risk_conversations():
    source = RespondIoSource(instance="mirra")
    source._api_key = "test-key"

    conversations = [
        _conv(id=1, labels=["escalated"]),      # customer_risk → included
        _conv(id=2, labels=[]),                  # no risk → skipped
        _conv(id=3, csat=1),                     # customer_risk → included
        _conv(id=4, status="resolved"),           # resolved, no label → skipped
    ]

    with patch.object(source, "_list_conversations", new=AsyncMock(return_value=conversations)):
        captures = await source.fetch()

    assert len(captures) == 2
    assert all(nc.source_type == "respondio" for nc in captures)
    assert {nc.external_id for nc in captures} == {"respondio_1", "respondio_3"}
