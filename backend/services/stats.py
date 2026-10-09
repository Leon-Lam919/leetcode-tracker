"""Numbers for the dashboard: today's status, streaks, totals, and the heatmap."""

import json
from collections import Counter
from datetime import date, timedelta

from sqlmodel import Session, select

from config import settings
from models.schemas import HeatmapDay, Stats
from models.tables import Problem, Solve
from services.streaks import current_streak, longest_streak

DIFFICULTIES = ["Easy", "Medium", "Hard"]


def get_stats(session: Session, today: date) -> Stats:
    solve_dates = list(session.exec(select(Solve.solved_date)))
    today_count = solve_dates.count(today)

    # Totals count distinct problems, not solves: re-solving Two Sum doesn't add to the total.
    solved_problems = session.exec(
        select(Problem).where(Problem.id.in_(select(Solve.problem_id)))
    ).all()

    by_difficulty = {difficulty: 0 for difficulty in DIFFICULTIES}
    topic_counts = Counter()
    for problem in solved_problems:
        by_difficulty[problem.difficulty] = by_difficulty.get(problem.difficulty, 0) + 1
        topic_counts.update(json.loads(problem.topics))

    return Stats(
        today_done=today_count >= settings.daily_goal,
        today_count=today_count,
        daily_goal=settings.daily_goal,
        current_streak=current_streak(solve_dates, today, settings.daily_goal),
        longest_streak=longest_streak(solve_dates, settings.daily_goal),
        total_solved=len(solved_problems),
        by_difficulty=by_difficulty,
        by_topic=dict(topic_counts.most_common()),  # biggest first
    )


def get_heatmap(session: Session, today: date, days: int) -> list[HeatmapDay]:
    """One entry per day for the last `days` days (oldest first), including zero days."""
    start = today - timedelta(days=days - 1)
    dates_in_range = session.exec(select(Solve.solved_date).where(Solve.solved_date >= start))
    counts = Counter(dates_in_range)

    heatmap = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        heatmap.append(HeatmapDay(date=day, count=counts[day]))
    return heatmap
