"""Streak math.

These are pure functions: they take a list of solve dates (one entry per solve,
duplicates allowed, any order) and return numbers. No database access, so they
are easy to test.
"""

from collections import Counter
from datetime import date, timedelta

ONE_DAY = timedelta(days=1)


def counted_days(solve_dates: list[date], daily_goal: int = 1) -> set[date]:
    """Return the days that have at least `daily_goal` solves."""
    solves_per_day = Counter(solve_dates)
    return {day for day, count in solves_per_day.items() if count >= daily_goal}


def current_streak(solve_dates: list[date], today: date, daily_goal: int = 1) -> int:
    """Count consecutive counted days ending today.

    If today isn't done yet but yesterday was, the streak is still alive
    (you have until midnight), so we count back from yesterday instead.
    """
    days = counted_days(solve_dates, daily_goal)

    if today in days:
        day = today
    elif today - ONE_DAY in days:
        day = today - ONE_DAY
    else:
        return 0

    streak = 0
    while day in days:
        streak += 1
        day -= ONE_DAY
    return streak


def longest_streak(solve_dates: list[date], daily_goal: int = 1) -> int:
    """Return the longest run of consecutive counted days ever."""
    days = sorted(counted_days(solve_dates, daily_goal))

    longest = 0
    run = 0
    previous = None
    for day in days:
        # Extend the run if this day follows the previous one, otherwise start over.
        run = run + 1 if previous == day - ONE_DAY else 1
        longest = max(longest, run)
        previous = day
    return longest
