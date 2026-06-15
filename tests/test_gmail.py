import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.classifier import ClassificationResult
from app.services.capture_service import create_capture_from_source
from app.sources.models import NormalizedCapture


def _make_nc(external_id: str = "msg-001", content: str = "Subject: Test\n\nFrom: a@b.com\n\nSnippet:\nHello") -> NormalizedCapture:
    return NormalizedCapture(
        source_type="gmail",
        source_instance="test@gmail.com",
        external_id=external_id,
        content=content,
        created_at=datetime.now(timezone.utc),
        metadata={"subject": "Test", "from": "a@b.com"},
    )


def _mock_db(existing=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = existing
    db.refresh.side_effect = lambda obj: setattr(obj, "id", 1) if not getattr(obj, "id", None) else None
    return db


async def test_gmail_sync_creates_capture():
    """Each fetched email that is not a duplicate becomes a Compass capture."""
    nc = _make_nc()
    db = _mock_db(existing=None)

    with patch("app.services.capture_service._classifier") as mock_clf, \
         patch("app.services.capture_service.create_inbox_task", new_callable=AsyncMock) as mock_cu:
        mock_clf.classify = AsyncMock(return_value=None)
        mock_cu.return_value = "clickup-task-id"
        capture = await create_capture_from_source(db, nc)

    assert capture is not None
    assert capture.source_type == "gmail"
    assert capture.source_instance == "test@gmail.com"
    assert capture.external_id == "msg-001"
    db.add.assert_called_once()


async def test_duplicate_email_not_imported():
    """An email whose external_id already exists in the DB is skipped."""
    nc = _make_nc(external_id="already-exists")
    db = _mock_db(existing=MagicMock())  # simulate existing capture

    capture = await create_capture_from_source(db, nc)

    assert capture is None
    db.add.assert_not_called()


async def test_imported_email_classified():
    """Imported emails go through classification and fields are persisted."""
    nc = _make_nc(
        external_id="msg-002",
        content="Subject: Invoice overdue\n\nFrom: accounting@example.com\n\nSnippet:\nYour invoice is 30 days overdue.",
    )
    db = _mock_db(existing=None)

    classification = ClassificationResult(
        type="Alert",
        domain="Mirra",
        priority="Critical",
        confidence=95,
        reasoning="Overdue invoice requires immediate financial attention.",
        attention_required=True,
        attention_reason="Overdue invoice requires immediate action.",
    )

    with patch("app.services.capture_service._classifier") as mock_clf, \
         patch("app.services.capture_service.create_inbox_task", new_callable=AsyncMock) as mock_cu:
        mock_clf.classify = AsyncMock(return_value=classification)
        mock_cu.return_value = None
        capture = await create_capture_from_source(db, nc)

    assert capture.classification_type == "Alert"
    assert capture.classification_priority == "Critical"
    assert capture.classification_confidence == 95
