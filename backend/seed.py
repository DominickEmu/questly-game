from database import SessionLocal
from models import ShopItem, Profile

DEFAULT_ITEMS = [
    {
        "name": "Flame Sword Avatar",
        "description": "A blazing sword icon for your profile.",
        "category": "avatar",
        "price_coins": 50,
        "price_gems": 0,
    },
    {
        "name": "Shadow Cloak Avatar",
        "description": "A mysterious dark cloak avatar.",
        "category": "avatar",
        "price_coins": 100,
        "price_gems": 5,
    },
    {
        "name": "Golden Shield Avatar",
        "description": "A shining golden shield for the brave.",
        "category": "avatar",
        "price_coins": 150,
        "price_gems": 8,
    },
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
    {
        "name": "Custom Quest Theme",
        "description": "Unlock a custom color theme for your quests.",
        "category": "custom",
        "price_coins": 80,
        "price_gems": 3,
    },
    {
        "name": "Title: Dragon Slayer",
        "description": "Display the title 'Dragon Slayer' on your profile.",
        "category": "custom",
        "price_coins": 120,
        "price_gems": 6,
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
