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
    equipped_hat: int | None
    equipped_face: int | None
    equipped_body: int | None
    equipped_hand: int | None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    username: str | None = None
    genre_preference: str | None = None
    equipped_hat: int | None = None
    equipped_face: int | None = None
    equipped_body: int | None = None
    equipped_hand: int | None = None


# ── Tasks ────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    difficulty: str = "medium"
    category: str | None = None
    due_date: date | None = None
    recurrence: str = "none"
    story_ender: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: str | None = None
    status: str | None = None
    category: str | None = None
    due_date: date | None = None
    recurrence: str | None = None
    story_ender: bool | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    difficulty: str
    status: str
    category: str | None
    due_date: date | None
    recurrence: str
    story_ender: bool
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
    story: str | None = None


# ── Story ───────────────────────────────────────────────

class StorySegmentOut(BaseModel):
    id: int
    task_id: int
    content: str
    genre: str
    created_at: datetime

    model_config = {"from_attributes": True}


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
