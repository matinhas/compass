from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.briefing import BriefingResponse
from app.services.briefing import generate_daily_briefing

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("", response_model=BriefingResponse)
def get_briefing(db: Session = Depends(get_db)):
    return generate_daily_briefing(db)
