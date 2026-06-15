import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.integration import GmailSyncRequest, GmailSyncResponse
from app.services.capture_service import create_capture_from_source
from app.sources.gmail import GmailSource

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
