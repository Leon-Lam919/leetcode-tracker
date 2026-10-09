from datetime import date, timedelta

import pytest

from services.review_schedule import INTERVALS, LAST_INDEX, next_state

TODAY = date(2026, 10, 8)


def in_days(n: int) -> date:
    return TODAY + timedelta(days=n)


@pytest.mark.parametrize(
    ("index", "confidence", "expected"),
    [
        (2, 1, (0, in_days(1))),  # again: start over
        (0, 1, (0, in_days(1))),
        (0, 2, (1, in_days(3))),  # good: +1
        (0, None, (1, in_days(3))),  # no confidence counts as good
        (0, 3, (2, in_days(7))),  # easy: +2
        (1, 2, (2, in_days(7))),
        (2, 3, (4, in_days(30))),
    ],
)
def test_each_confidence(index, confidence, expected):
    assert next_state(index, confidence, TODAY) == expected


def test_easy_is_capped_at_last_interval():
    assert next_state(LAST_INDEX - 1, 3, TODAY) == (LAST_INDEX, in_days(INTERVALS[-1]))


@pytest.mark.parametrize("confidence", [2, 3, None])
def test_good_review_at_last_interval_is_mastered(confidence):
    assert next_state(LAST_INDEX, confidence, TODAY) == (LAST_INDEX, None)


def test_again_at_last_interval_starts_over():
    assert next_state(LAST_INDEX, 1, TODAY) == (0, in_days(1))


def test_invalid_confidence_raises():
    with pytest.raises(ValueError):
        next_state(0, 4, TODAY)
