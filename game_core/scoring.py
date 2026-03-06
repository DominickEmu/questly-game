import random
from datetime import date
from typing import Tuple

from .models import Task, UserStats, TaskType, Difficulty


def is_due_on(task: Task, target: date) -> bool:
    """
    Mirror of your desktop app's date logic, but using the Pydantic Task.
    """
    if task.task_type == TaskType.ONESHOT:
        if not task.due_date:
            return False
        return task.due_date == target

    if task.task_type == TaskType.WEEKLY:
        if not task.start_date or not task.days_of_week:
            return False

        if target < task.start_date:
            return False

        if target.weekday() not in task.days_of_week:
            return False

        days_diff = (target - task.start_date).days
        weeks_diff = days_diff // 7
        return weeks_diff % task.repeat_frequency == 0

    return False


def base_xp_for_difficulty(difficulty: Difficulty) -> int:
    if difficulty == Difficulty.EASY:
        return 8
    if difficulty == Difficulty.MEDIUM:
        return 15
    if difficulty == Difficulty.HARD:
        return 25
    return 10


def currency_drop_for_task(task: Task) -> Tuple[int, int, int]:
    """
    Returns (coins, rubies, scrap) gained for completing a task.

    Rules:
    - Coins: always granted, more for higher difficulty.
    - Scrap: common on easy, less on hard.
    - Rubies: probabilistic, with higher chance on harder tasks.
    """
    if task.difficulty == Difficulty.EASY:
        coins = 5
        scrap = 3
        ruby_chance = 0.05
    elif task.difficulty == Difficulty.MEDIUM:
        coins = 10
        scrap = 2
        ruby_chance = 0.15
    else:  # HARD
        coins = 18
        scrap = 1
        ruby_chance = 0.35

    rubies = 1 if random.random() < ruby_chance else 0
    return coins, rubies, scrap


def apply_completion_rewards(task: Task, stats: UserStats) -> Tuple[UserStats, dict]:
    """
    Apply XP and currency rewards for a completed task.

    Returns updated stats and a dict of deltas:
      { "xp": int, "coins": int, "rubies": int, "scrap": int, "leveled_up": bool }
    """
    before = stats.copy()

    # XP
    xp_gain = base_xp_for_difficulty(task.difficulty)
    stats.xp += xp_gain

    # Currencies
    coins_gain, rubies_gain, scrap_gain = currency_drop_for_task(task)
    stats.coins += coins_gain
    stats.rubies += rubies_gain
    stats.scrap += scrap_gain

    # Level up loop
    leveled_up = False
    while stats.xp >= stats.xp_to_next:
        stats.xp -= stats.xp_to_next
        stats.level += 1
        stats.xp_to_next = int(stats.xp_to_next * 1.25)
        leveled_up = True

    deltas = {
        "xp": stats.xp - before.xp + (before.xp_to_next - before.xp if leveled_up else 0),
        "coins": coins_gain,
        "rubies": rubies_gain,
        "scrap": scrap_gain,
        "leveled_up": leveled_up,
    }

    return stats, deltas

