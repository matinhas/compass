from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.capture import CaptureCreate, CaptureResponse
from app.services.capture_service import create_capture, list_captures

router = APIRouter(prefix="/captures", tags=["captures"])


@router.post("", response_model=CaptureResponse, status_code=201)
async def create(data: CaptureCreate, db: Session = Depends(get_db)):
    return await create_capture(db, data)


@router.get("", response_model=list[CaptureResponse])
def list_all(db: Session = Depends(get_db)):
    return list_captures(db)
