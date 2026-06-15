import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.integration import GmailSyncRequest, GmailSyncResponse, RespondIoSyncResponse
from app.services.capture_service import create_capture_from_source
from app.sources.gmail import GmailSource
from app.sources.respondio import RespondIoSource

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/gmail/sync", response_model=GmailSyncResponse)
async def gmail_sync(body: GmailSyncRequest, db: Session = Depends(get_db)):
    source = GmailSource(account=body.account)

    try:
        normalized = await source.fetch()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Gmail API error: {e.response.status_code} — check credentials in Railway")

    created = 0
    for nc in normalized:
        result = await create_capture_from_source(db, nc)
        if result is not None:
            created += 1

    return GmailSyncResponse(emails_processed=len(normalized), captures_created=created)


@router.post("/respondio/sync", response_model=RespondIoSyncResponse)
async def respondio_sync(db: Session = Depends(get_db)):
    source = RespondIoSource(instance="mirra")

    try:
        risk_captures = await source.fetch()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"respond.io API error: {e.response.status_code} — check RESPONDIO_API_KEY in Railway")

    created = 0
    for nc in risk_captures:
        result = await create_capture_from_source(db, nc)
        if result is not None:
            created += 1

    return RespondIoSyncResponse(
        conversations_scanned=source.conversations_scanned,
        risk_events_found=len(risk_captures),
        captures_created=created,
    )
