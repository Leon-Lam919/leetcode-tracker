from datetime import date, timedelta

from services.streaks import current_streak, longest_streak

TODAY = date(2026, 10, 8)


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def test_empty_list_is_zero():
    assert current_streak([], TODAY) == 0
    assert longest_streak([]) == 0


def test_only_today():
    dates = [TODAY]
    assert current_streak(dates, TODAY) == 1
    assert longest_streak(dates) == 1


def test_yesterday_only_keeps_streak_alive():
    assert current_streak([days_ago(1)], TODAY) == 1


def test_gap_of_two_days_breaks_streak():
    # Last solve was 2 days ago, so neither today nor yesterday counts.
    assert current_streak([days_ago(2), days_ago(3)], TODAY) == 0


def test_unsorted_with_duplicates():
    dates = [days_ago(1), TODAY, days_ago(2), TODAY, days_ago(1)]
    assert current_streak(dates, TODAY) == 3
    assert longest_streak(dates) == 3


def test_longest_run_in_the_past_is_bigger_than_current():
    past_run = [days_ago(n) for n in range(10, 15)]  # 5 days in a row
    recent_run = [days_ago(1), TODAY]  # 2 days in a row
    dates = past_run + recent_run
    assert current_streak(dates, TODAY) == 2
    assert longest_streak(dates) == 5


def test_daily_goal_of_two_ignores_days_with_one_solve():
    dates = [TODAY]  # only one solve today
    assert current_streak(dates, TODAY, daily_goal=2) == 0
    assert longest_streak(dates, daily_goal=2) == 0

    dates = [TODAY, TODAY]
    assert current_streak(dates, TODAY, daily_goal=2) == 1
