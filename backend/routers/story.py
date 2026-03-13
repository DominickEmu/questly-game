from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import StorySegment
from schemas import StorySegmentOut

router = APIRouter(prefix="/story", tags=["story"])


@router.get("", response_model=list[StorySegmentOut])
def get_story(db: Session = Depends(get_db)):
    return (
        db.query(StorySegment)
        .order_by(StorySegment.created_at.asc())
        .all()
    )


@router.post("/reset", status_code=204)
def reset_story(db: Session = Depends(get_db)):
    db.query(StorySegment).delete()
    db.commit()
