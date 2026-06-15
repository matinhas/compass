from pydantic import BaseModel


class GmailSyncRequest(BaseModel):
    account: str


class GmailSyncResponse(BaseModel):
    emails_processed: int
    captures_created: int


class RespondIoSyncResponse(BaseModel):
    conversations_scanned: int
    risk_events_found: int
    captures_created: int
