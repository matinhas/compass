from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.attention import AttentionResponse
from app.services.attention import generate_attention_ranking

router = APIRouter(prefix="/attention", tags=["attention"])


@router.get("", response_model=AttentionResponse)
def get_attention(db: Session = Depends(get_db)):
    return generate_attention_ranking(db)
