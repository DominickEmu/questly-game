from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Task, Profile
from schemas import TaskCreate, TaskUpdate, TaskOut, RewardOut
from story_generator import generate_story_segment

router = APIRouter(tags=["tasks"])

REWARD_TABLE = {
    "easy":    {"xp": 10,  "coins": 5,  "gems": 0},
    "medium":  {"xp": 25,  "coins": 15, "gems": 1},
    "hard":    {"xp": 50,  "coins": 30, "gems": 3},
    "extreme": {"xp": 100, "coins": 60, "gems": 5},
}

XP_PER_LEVEL = 100


def _get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _clone_recurring_task(db: Session, original: Task) -> Task | None:
    if original.recurrence == "none":
        return None

    delta = timedelta(days=1) if original.recurrence == "daily" else timedelta(weeks=1)
    next_due = (original.due_date or date.today()) + delta

    clone = Task(
        title=original.title,
        description=original.description,
        difficulty=original.difficulty,
        status="pending",
        category=original.category,
        due_date=next_due,
        recurrence=original.recurrence,
    )
    db.add(clone)
    return clone


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    due_date: date | None = None,
    recurrence: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    if due_date:
        q = q.filter(Task.due_date == due_date)
    if recurrence:
        q = q.filter(Task.recurrence == recurrence)
    return q.order_by(Task.created_at.desc()).all()


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**body.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()


@router.post("/tasks/{task_id}/complete", response_model=RewardOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status == "completed":
        raise HTTPException(400, "Task already completed")

    task.status = "completed"
    task.completed_at = datetime.utcnow()

    clone = _clone_recurring_task(db, task)

    rewards = REWARD_TABLE.get(task.difficulty, REWARD_TABLE["medium"])
    profile = _get_or_create_profile(db)

    profile.xp += rewards["xp"]
    profile.coins += rewards["coins"]
    profile.gems += rewards["gems"]

    leveled_up = False
    while profile.xp >= XP_PER_LEVEL * profile.level:
        profile.xp -= XP_PER_LEVEL * profile.level
        profile.level += 1
        leveled_up = True

    # Commit core task + reward changes before attempting story generation
    db.commit()
    db.refresh(profile)
    if clone:
        db.refresh(clone)

    # Try to generate a story segment, but never block rewards if it fails
    story = generate_story_segment(db, task, profile)

    return RewardOut(
        xp=rewards["xp"],
        coins=rewards["coins"],
        gems=rewards["gems"],
        leveled_up=leveled_up,
        new_level=profile.level,
        next_task_id=clone.id if clone else None,
        story=story,
    )
