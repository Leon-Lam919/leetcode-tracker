"""The GitHub Actions reminder script (scripts/daily_check.py).

LeetCode is faked by the `fake_leetcode` fixture and ntfy by a respx route, so
nothing real is ever sent. "Now" is frozen by patching clock.utc_now.
"""

from datetime import UTC, datetime

import httpx
import pytest

from config import settings
from scripts import daily_check
from services import clock

NTFY_URL = "https://ntfy.example.test/my-secret-topic"

# recent_ac.json in Chicago time: three solves on 2026-10-08 and one on 2026-10-07.
DONE_DAY = datetime(2026, 10, 8, 23, 0, tzinfo=UTC)  # 6pm Chicago, Oct 8
NEXT_DAY = datetime(2026, 10, 9, 23, 0, tzinfo=UTC)  # Oct 9, nothing solved yet
MUCH_LATER = datetime(2026, 10, 12, 23, 0, tzinfo=UTC)  # streak already broken


@pytest.fixture(autouse=True)
def env(monkeypatch):
    """Script env vars. Patching settings first makes monkeypatch undo the script's changes."""
    for field in ("tz", "ntfy_topic", "ntfy_server"):
        monkeypatch.setattr(settings, field, getattr(settings, field))
    monkeypatch.setenv("LEETCODE_USERNAME", "testuser")
    monkeypatch.setenv("TZ", "America/Chicago")
    monkeypatch.setenv("NTFY_SERVER", "https://ntfy.example.test")
    monkeypatch.setenv("NTFY_TOPIC", "my-secret-topic")


@pytest.fixture
def ntfy(fake_leetcode):
    return fake_leetcode.router.post(NTFY_URL).mock(return_value=httpx.Response(200))


def freeze(monkeypatch, moment: datetime) -> None:
    monkeypatch.setattr(clock, "utc_now", lambda: moment)


def sent_message(route) -> str:
    return route.calls.last.request.content.decode()


def test_done_today_sends_nothing(monkeypatch, ntfy, capsys):
    freeze(monkeypatch, DONE_DAY)

    assert daily_check.main([]) == 0

    assert ntfy.call_count == 0
    assert "✅ solved today: Valid Parentheses, Two Sum" in capsys.readouterr().out


def test_not_done_sends_with_streak(monkeypatch, ntfy):
    freeze(monkeypatch, NEXT_DAY)

    assert daily_check.main([]) == 0

    assert ntfy.call_count == 1
    assert ntfy.calls.last.request.headers["Title"] == "LeetCode reminder"
    assert sent_message(ntfy) == "No LeetCode yet today. 🔥 2-day streak at risk."


def test_no_streak_says_start_a_new_one(monkeypatch, ntfy):
    freeze(monkeypatch, MUCH_LATER)

    assert daily_check.main([]) == 0

    assert sent_message(ntfy) == "No LeetCode yet today. Start a new streak!"


def test_late_evening_solve_counts_for_that_local_day(monkeypatch, ntfy, fake_leetcode):
    # 11:30pm Chicago on Oct 8 is already 04:30 UTC on Oct 9.
    solved = datetime(2026, 10, 9, 4, 30, tzinfo=UTC)
    fake_leetcode.recent_response = {
        "data": {
            "recentAcSubmissionList": [
                {
                    "title": "Two Sum",
                    "titleSlug": "two-sum",
                    "timestamp": str(int(solved.timestamp())),
                }
            ]
        }
    }
    freeze(monkeypatch, datetime(2026, 10, 9, 4, 45, tzinfo=UTC))  # 11:45pm Chicago, Oct 8

    assert daily_check.main([]) == 0
    assert ntfy.call_count == 0


def test_leetcode_error_sends_fallback_and_fails(monkeypatch, ntfy, fake_leetcode):
    freeze(monkeypatch, NEXT_DAY)
    fake_leetcode.down = True

    assert daily_check.main([]) == 1

    assert sent_message(ntfy) == "Couldn't check LeetCode today. Solve one anyway!"


def test_dry_run_never_sends(monkeypatch, ntfy, fake_leetcode, capsys):
    monkeypatch.delenv("NTFY_TOPIC")  # not needed for a dry run
    freeze(monkeypatch, NEXT_DAY)

    assert daily_check.main(["--dry-run"]) == 0
    fake_leetcode.down = True
    assert daily_check.main(["--dry-run", "--force"]) == 1

    assert ntfy.call_count == 0
    out = capsys.readouterr().out
    assert "[dry-run] would send: 'LeetCode reminder': No LeetCode yet today. 🔥 2-day" in out
    assert "[dry-run] would send: 'LeetCode reminder': Couldn't check LeetCode" in out


def test_force_sends_even_when_done(monkeypatch, ntfy):
    freeze(monkeypatch, DONE_DAY)

    assert daily_check.main(["--force"]) == 0

    assert ntfy.call_count == 1
    assert "already solved today, 2-day streak" in sent_message(ntfy)


def test_ntfy_failure_exits_1_with_a_message(monkeypatch, fake_leetcode, capsys):
    fake_leetcode.router.post(NTFY_URL).mock(return_value=httpx.Response(500))
    freeze(monkeypatch, NEXT_DAY)

    assert daily_check.main([]) == 1
    assert "ntfy failed" in capsys.readouterr().err


@pytest.mark.parametrize("missing", ["LEETCODE_USERNAME", "NTFY_TOPIC"])
def test_missing_config_exits_2(monkeypatch, ntfy, fake_leetcode, missing, capsys):
    monkeypatch.delenv(missing)

    assert daily_check.main([]) == 2

    assert missing in capsys.readouterr().err
    assert fake_leetcode.calls == [] and ntfy.call_count == 0


def test_tz_defaults_to_chicago(monkeypatch):
    monkeypatch.delenv("TZ")
    daily_check.load_env(dry_run=False)
    assert settings.tz == "America/Chicago"
