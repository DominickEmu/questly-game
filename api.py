from datetime import date, datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from game_core import (
    Task,
    TaskCreate,
    TaskType,
    Difficulty,
    Label,
    UserStats,
    is_due_on,
    apply_completion_rewards,
)


app = FastAPI(title="Questly Game API", version="0.1.0")


# --- In-memory storage for now ------------------------------------------------

TASKS: Dict[int, Task] = {}
LABELS: Dict[int, Label] = {}
USER_STATS = UserStats()

_task_id_counter = 0
_label_id_counter = 0


def next_task_id() -> int:
    global _task_id_counter
    _task_id_counter += 1
    return _task_id_counter


def next_label_id() -> int:
    global _label_id_counter
    _label_id_counter += 1
    return _label_id_counter


# --- Pydantic helper models ---------------------------------------------------


class LabelCreate(BaseModel):
    name: str
    symbol: str = "📋"
    color: str = "#8B7355"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    labels: List[int] | None = None
    task_type: TaskType | None = None
    difficulty: Difficulty | None = None
    due_date: date | None = None
    days_of_week: List[int] | None = None
    start_date: date | None = None
    repeat_frequency: int | None = None


class CompletionResult(BaseModel):
    task: Task
    stats: UserStats
    xp: int
    coins: int
    rubies: int
    scrap: int
    leveled_up: bool


# --- Routes -------------------------------------------------------------------


@app.get("/me", response_model=UserStats)
def get_me() -> UserStats:
    return USER_STATS


@app.get("/labels", response_model=List[Label])
def list_labels() -> List[Label]:
    return list(LABELS.values())


@app.post("/labels", response_model=Label)
def create_label(payload: LabelCreate) -> Label:
    new_id = next_label_id()
    label = Label(id=new_id, **payload.dict())
    LABELS[new_id] = label
    return label


@app.get("/tasks", response_model=List[Task])
def list_tasks(view: str = "today") -> List[Task]:
    """
    view=today  -> tasks due today
    view=week   -> all tasks due this week (simple: all tasks for now)
    view=all    -> all tasks
    """
    today = date.today()
    if view == "today":
        return [t for t in TASKS.values() if is_due_on(t, today)]
    elif view == "week":
        # For now, just return all tasks; a more precise week filter can be added
        return list(TASKS.values())
    else:
        return list(TASKS.values())


@app.post("/tasks", response_model=Task)
def create_task(payload: TaskCreate) -> Task:
    new_id = next_task_id()
    task = Task(
        id=new_id,
        created_at=datetime.utcnow(),
        completed=False,
        **payload.dict(),
    )
    TASKS[new_id] = task
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    existing = TASKS[task_id]
    data = payload.dict(exclude_unset=True)
    updated = existing.copy(update=data)
    TASKS[task_id] = updated
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    del TASKS[task_id]


@app.post("/tasks/{task_id}/complete", response_model=CompletionResult)
def complete_task(task_id: int) -> CompletionResult:
    global USER_STATS

    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    task = TASKS[task_id]
    if task.completed:
        raise HTTPException(status_code=400, detail="Task already completed")

    task.completed = True
    TASKS[task_id] = task

    USER_STATS, rewards = apply_completion_rewards(task, USER_STATS)

    return CompletionResult(
        task=task,
        stats=USER_STATS,
        xp=rewards["xp"],
        coins=rewards["coins"],
        rubies=rewards["rubies"],
        scrap=rewards["scrap"],
        leveled_up=rewards["leveled_up"],
    )


@app.get("/")
def root() -> dict:
    return {"message": "Questly Game API is running"}

