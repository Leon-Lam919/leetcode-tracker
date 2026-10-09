"""Spaced repetition: when should you look at a problem again?

A pure function with no database access, so every rule is easy to test.
Each problem has an `interval_index` into INTERVALS. A good review moves it
forward (longer gap), a bad one sends it back to the start.
"""

from datetime import date, timedelta

INTERVALS = [1, 3, 7, 14, 30]  # days until the next review
LAST_INDEX = len(INTERVALS) - 1

AGAIN, GOOD, EASY = 1, 2, 3  # the confidence values (same scale as a solve's confidence)


def next_state(interval_index: int, confidence: int | None, today: date) -> tuple[int, date | None]:
    """Return (new_index, next_review_date) after a review on `today`.

    - confidence 1 (again): start over at index 0
    - confidence 2 or None (good): move forward 1
    - confidence 3 (easy): move forward 2
    The index is capped at the last interval. A good or easy review when the
    problem is *already* at the last interval means it is mastered: next date None.
    """
    if confidence not in (None, AGAIN, GOOD, EASY):
        raise ValueError(f"confidence must be 1, 2, 3 or None, not {confidence!r}")

    if confidence == AGAIN:
        new_index = 0
    elif interval_index >= LAST_INDEX:
        return LAST_INDEX, None  # mastered
    else:
        step = 2 if confidence == EASY else 1
        new_index = min(interval_index + step, LAST_INDEX)

    return new_index, today + timedelta(days=INTERVALS[new_index])
