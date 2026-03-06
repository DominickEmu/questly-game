from datetime import datetime, date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class TaskType(str, Enum):
    ONESHOT = "oneshot"
    WEEKLY = "weekly"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Label(BaseModel):
    id: int
    name: str
    symbol: str = "📋"
    color: str = "#8B7355"


class TaskBase(BaseModel):
    title: str
    description: str = ""
    labels: List[int] = []  # label IDs
    task_type: TaskType = TaskType.ONESHOT
    difficulty: Difficulty = Difficulty.MEDIUM

    # Oneshoot
    due_date: Optional[date] = None

    # Weekly
    days_of_week: List[int] = []  # 0=Monday, 6=Sunday
    start_date: Optional[date] = None
    repeat_frequency: int = 1  # every N weeks


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: int
    completed: bool = False
    created_at: datetime

    class Config:
        orm_mode = True


class UserStats(BaseModel):
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100

    coins: int = 0   # general currency
    rubies: int = 0  # rare / premium currency
    scrap: int = 0   # common crafting currency

    hp: int = 100

