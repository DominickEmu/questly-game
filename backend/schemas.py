from datetime import datetime, date
from pydantic import BaseModel


# ── Profile ──────────────────────────────────────────────

class ProfileOut(BaseModel):
    id: int
    username: str
    level: int
    xp: int
    coins: int
    gems: int
    genre_preference: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    username: str | None = None
    genre_preference: str | None = None


# ── Tasks ────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    difficulty: str = "medium"
    category: str | None = None
    due_date: date | None = None
    recurrence: str = "none"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: str | None = None
    status: str | None = None
    category: str | None = None
    due_date: date | None = None
    recurrence: str | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    difficulty: str
    status: str
    category: str | None
    due_date: date | None
    recurrence: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RewardOut(BaseModel):
    xp: int
    coins: int
    gems: int
    leveled_up: bool
    new_level: int
    next_task_id: int | None = None


# ── Shop ─────────────────────────────────────────────────

class ShopItemOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price_coins: int
    price_gems: int
    image_url: str | None

    model_config = {"from_attributes": True}


class PurchaseOut(BaseModel):
    id: int
    shop_item_id: int
    purchased_at: datetime
    item: ShopItemOut

    model_config = {"from_attributes": True}
