from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Profile
from schemas import ProfileOut, ProfileUpdate

router = APIRouter(tags=["profile"])


def _get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    return _get_or_create_profile(db)


@router.put("/profile", response_model=ProfileOut)
def update_profile(body: ProfileUpdate, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/profile/dev", response_model=ProfileOut)
def dev_add_currency(db: Session = Depends(get_db)):
    """Dev/testing only: add 999 coins and 999 gems."""
    profile = _get_or_create_profile(db)
    profile.coins += 999
    profile.gems += 999
    db.commit()
    db.refresh(profile)
    return profile
