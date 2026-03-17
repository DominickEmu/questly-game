from database import SessionLocal
from models import ShopItem, Profile

DEFAULT_ITEMS = [
    # ── Hats ─────────────────────────────────────────────
    {
        "name": "Detective Hat",
        "description": "A weathered felt hat worn by those who uncover the truth.",
        "category": "hat",
        "price_coins": 75,
        "price_gems": 0,
        "image_url": "/images/avatar_hat_detectivehat.png",
    },
    {
        "name": "Wizard Hat",
        "description": "A towering hat crackling with arcane energy.",
        "category": "hat",
        "price_coins": 120,
        "price_gems": 5,
        "image_url": "/images/avatar_hat_wizardhat.png",
    },
    # ── Face ─────────────────────────────────────────────
    {
        "name": "Glasses",
        "description": "Round spectacles that sharpen your gaze and your wit.",
        "category": "face",
        "price_coins": 50,
        "price_gems": 0,
        "image_url": "/images/avatar_face_glasses.png",
    },
    {
        "name": "Sci Visor",
        "description": "A sleek heads-up display from a distant technological era.",
        "category": "face",
        "price_coins": 90,
        "price_gems": 3,
        "image_url": "/images/avatar_face_scivisor.png",
    },
    # ── Body ─────────────────────────────────────────────
    {
        "name": "Robe",
        "description": "Flowing robes adorned with the crests of ancient academies.",
        "category": "body",
        "price_coins": 100,
        "price_gems": 0,
        "image_url": "/images/avatar_body_robe.png",
    },
    {
        "name": "Ghost Cloak",
        "description": "A translucent shroud that lets you slip between the living and the dead.",
        "category": "body",
        "price_coins": 180,
        "price_gems": 8,
        "image_url": "/images/avatar_body_ghost.png",
    },
    # ── Hand ─────────────────────────────────────────────
    {
        "name": "Staff",
        "description": "A gnarled wooden staff pulsing with residual magic.",
        "category": "hand",
        "price_coins": 80,
        "price_gems": 2,
        "image_url": "/images/avatar_hand_staff.png",
    },
    # ── Rewards ──────────────────────────────────────────
    {
        "name": "Break Potion",
        "description": "Redeem for a 15-minute guilt-free break!",
        "category": "reward",
        "price_coins": 30,
        "price_gems": 0,
    },
    {
        "name": "Snack Scroll",
        "description": "Treat yourself to a snack of your choice.",
        "category": "reward",
        "price_coins": 40,
        "price_gems": 0,
    },
    {
        "name": "Movie Night Ticket",
        "description": "One movie night, no questions asked.",
        "category": "reward",
        "price_coins": 200,
        "price_gems": 10,
    },
]


def seed_defaults():
    db = SessionLocal()
    try:
        if db.query(ShopItem).count() == 0:
            for data in DEFAULT_ITEMS:
                db.add(ShopItem(**data))
            db.commit()

        if not db.get(Profile, 1):
            db.add(Profile(id=1))
            db.commit()
    finally:
        db.close()
