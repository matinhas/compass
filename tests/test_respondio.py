from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.sources.respondio import RespondIoSource, _detect_risk, _build_capture


def _contact(
    id: int = 1,
    status: str = "open",
    tags: list = None,
    created_days_ago: int = 1,
    first_name: str = "Test",
    last_name: str = "Contact",
) -> dict:
    created_ts = int((datetime.now(timezone.utc) - timedelta(days=created_days_ago)).timestamp())
    return {
        "id": id,
        "status": status,
        "tags": tags or [],
        "created_at": created_ts,
        "firstName": first_name,
        "lastName": last_name,
        "phone": "+351910000000",
        "email": None,
        "lifecycle": "Booked",
    }


def test_customer_risk_tag():
    assert _detect_risk(_contact(tags=["escalated"])) == "customer_risk"


def test_no_matching_tag_not_risk():
    assert _detect_risk(_contact(tags=["booking-confirmed"])) is None


def test_staff_risk_tag():
    assert _detect_risk(_contact(tags=["misconduct"])) == "staff_risk"


def test_operational_risk_tag():
    assert _detect_risk(_contact(tags=["outage"])) == "operational_risk"


def test_unresolved_3_days_is_operational_risk():
    assert _detect_risk(_contact(status="open", created_days_ago=4)) == "operational_risk"


def test_unresolved_1_day_not_risk():
    assert _detect_risk(_contact(status="open", created_days_ago=1)) is None


def test_closed_old_contact_not_risk():
    assert _detect_risk(_contact(status="closed", created_days_ago=10)) is None


def test_no_risk_contact_skipped():
    assert _detect_risk(_contact(tags=[], status="open", created_days_ago=1)) is None


def test_build_capture_sets_correct_fields():
    contact = _contact(id=42, tags=["escalated"])
    nc = _build_capture(contact, "customer_risk", "mirra")

    assert nc.source_type == "respondio"
    assert nc.source_instance == "mirra"
    assert nc.external_id == "respondio_42"
    assert nc.metadata["risk_type"] == "customer_risk"
    assert nc.metadata["conversation_id"] == 42
    assert "Customer Risk" in nc.content
    assert "Test Contact" in nc.content


def test_build_capture_contact_name_from_name_fields():
    contact = _contact(id=1, first_name="Ana", last_name="Silva")
    nc = _build_capture(contact, "staff_risk", "mirra")
    assert "Ana Silva" in nc.content


async def test_fetch_filters_only_risk_contacts():
    source = RespondIoSource(instance="mirra")
    source._api_key = "test-key"

    contacts = [
        _contact(id=1, tags=["escalated"]),    # customer_risk → included
        _contact(id=2, tags=[]),               # no risk → skipped
        _contact(id=3, tags=["outage"]),       # operational_risk → included
        _contact(id=4, status="closed"),       # closed, no tag → skipped
    ]

    with patch.object(source, "_list_contacts", new=AsyncMock(return_value=contacts)):
        captures = await source.fetch()

    assert len(captures) == 2
    assert all(nc.source_type == "respondio" for nc in captures)
    assert {nc.external_id for nc in captures} == {"respondio_1", "respondio_3"}
