from pydantic import BaseModel


class GmailSyncRequest(BaseModel):
    account: str


class GmailSyncResponse(BaseModel):
    emails_processed: int
    captures_created: int
