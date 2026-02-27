from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import ShopItem, Purchase, Profile
from schemas import ShopItemOut, PurchaseOut

router = APIRouter(tags=["shop"])


def _get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/shop", response_model=list[ShopItemOut])
def list_shop_items(db: Session = Depends(get_db)):
    return db.query(ShopItem).all()


@router.post("/shop/buy/{item_id}", response_model=PurchaseOut)
def buy_item(
    item_id: int,
    currency: str = Query("coins", pattern="^(coins|gems)$"),
    db: Session = Depends(get_db),
):
    item = db.get(ShopItem, item_id)
    if not item:
        raise HTTPException(404, "Item not found")

    profile = _get_or_create_profile(db)

    if currency == "coins":
        if item.price_coins <= 0:
            raise HTTPException(400, "Item cannot be purchased with coins")
        if profile.coins < item.price_coins:
            raise HTTPException(400, "Not enough coins")
        profile.coins -= item.price_coins
    else:
        if item.price_gems <= 0:
            raise HTTPException(400, "Item cannot be purchased with gems")
        if profile.gems < item.price_gems:
            raise HTTPException(400, "Not enough gems")
        profile.gems -= item.price_gems

    purchase = Purchase(shop_item_id=item.id)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/shop/purchases", response_model=list[PurchaseOut])
def list_purchases(db: Session = Depends(get_db)):
    return db.query(Purchase).order_by(Purchase.purchased_at.desc()).all()
