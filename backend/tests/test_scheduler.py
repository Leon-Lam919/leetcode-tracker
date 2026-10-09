"""Auto-sync, the evening reminder, notifications, and REMINDER_TIME parsing.

No real notification is ever sent: ntfy is faked with respx, and conftest sets
NTFY_TOPIC to empty unless a test turns it on with the `ntfy` fixture.
"""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from config import Settings, settings
from services import clock, notify, scheduler
from services.clock import today_local

NTFY_URL = "https://ntfy.example.test/my-secret-topic"


@pytest.fixture
def ntfy(fake_leetcode, monkeypatch):
    """Turn notifications on, pointed at a fake ntfy server. Returns the respx route."""
    monkeypatch.setattr(settings, "ntfy_server", "https://ntfy.example.test/")
    monkeypatch.setattr(settings, "ntfy_topic", "my-secret-topic")
    return fake_leetcode.router.post(NTFY_URL).mock(return_value=httpx.Response(200))


@pytest.fixture
def logs():
    """Collect log messages written with loguru."""
    messages = []
    handler_id = logger.add(lambda message: messages.append(str(message)), level="INFO")
    yield messages
    logger.remove(handler_id)


def add_solve(client, days_ago=0):
    solved_date = (today_local() - timedelta(days=days_ago)).isoformat()
    body = {"title_slug": "two-sum", "title": "Two Sum", "difficulty": "Easy"}
    assert client.post("/api/solves", json={**body, "solved_date": solved_date}).status_code == 201


# --- Reminder ---------------------------------------------------------------


def test_reminder_sends_when_today_is_not_done(client, ntfy, fake_leetcode):
    fake_leetcode.recent_response = {"data": {"recentAcSubmissionList": []}}
    add_solve(client, days_ago=1)  # a 1-day streak, but nothing today

    assert scheduler.evening_reminder() is True

    assert ntfy.call_count == 1
    request = ntfy.calls.last.request
    assert request.headers["Title"] == "LeetCode reminder"
    assert request.content.decode() == "No LeetCode yet today. 🔥 1-day streak at risk."


def test_reminder_is_quiet_when_today_is_done(client, ntfy, fake_leetcode):
    fake_leetcode.recent_response = {"data": {"recentAcSubmissionList": []}}
    add_solve(client, days_ago=0)

    assert scheduler.evening_reminder() is False
    assert ntfy.call_count == 0


def test_reminder_syncs_first(client, ntfy, monkeypatch):
    # The fixture's submissions are on 2026-10-07/08 (Toronto); pretend it's 2026-10-08.
    monkeypatch.setattr(clock, "utc_now", lambda: datetime(2026, 10, 8, 23, 0, tzinfo=UTC))

    assert scheduler.evening_reminder() is False  # the sync found today's solves
    assert ntfy.call_count == 0


def test_reminder_message_without_a_streak():
    assert scheduler.reminder_message(0) == "No LeetCode yet today. Solve one to start a streak."


# --- Scheduled sync ---------------------------------------------------------


def test_scheduled_sync_updates_last_sync(client, monkeypatch):
    now = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(clock, "utc_now", lambda: now)

    result = scheduler.scheduled_sync()

    assert (result.added, result.skipped) == (3, 1)
    stats = client.get("/api/stats").json()
    assert stats["last_sync_at"] == "2026-10-09T12:00:00Z"
    assert stats["last_sync_result"] == "added 3, skipped 1"


def test_scheduled_sync_failure_is_caught_and_logged(client, fake_leetcode, logs):
    fake_leetcode.down = True

    assert scheduler.scheduled_sync() is None  # no exception escapes

    assert any("Scheduled sync failed" in message for message in logs)
    stats = client.get("/api/stats").json()
    assert stats["last_sync_result"].startswith("failed: could not reach LeetCode")
    assert client.get("/api/solves").json() == []


def test_scheduled_sync_without_username_is_skipped(client, monkeypatch, fake_leetcode):
    monkeypatch.setattr(settings, "leetcode_username", "")
    assert scheduler.scheduled_sync() is None
    assert fake_leetcode.calls == []


def test_manual_sync_also_records_last_sync(client):
    client.post("/api/sync")
    assert client.get("/api/stats").json()["last_sync_result"] == "added 3, skipped 1"


def test_build_scheduler_uses_settings(monkeypatch):
    monkeypatch.setattr(settings, "sync_interval_hours", 3)
    monkeypatch.setattr(settings, "reminder_time", "20:15")

    jobs = {job.id: job for job in scheduler.build_scheduler().get_jobs()}

    assert isinstance(jobs["sync"].trigger, IntervalTrigger)
    assert jobs["sync"].trigger.interval == timedelta(hours=3)
    reminder = jobs["reminder"].trigger
    assert isinstance(reminder, CronTrigger)
    assert str(reminder.timezone) == settings.tz
    fields = {field.name: str(field) for field in reminder.fields}
    assert (fields["hour"], fields["minute"]) == ("20", "15")


# --- Notifications ----------------------------------------------------------


def test_notify_skips_without_topic(fake_leetcode, logs):
    assert settings.ntfy_topic == ""
    assert notify.send("title", "message") is False
    assert any("NTFY_TOPIC is not set" in message for message in logs)


def test_notify_error_is_raised_as_notify_error(ntfy):
    ntfy.mock(return_value=httpx.Response(500))
    with pytest.raises(notify.NotifyError):
        notify.send("title", "message")


def test_notify_test_endpoint(client, ntfy):
    response = client.post("/api/notify/test")
    assert response.status_code == 200
    assert ntfy.call_count == 1


def test_notify_test_endpoint_without_topic_is_400(client):
    assert client.post("/api/notify/test").status_code == 400


# --- REMINDER_TIME ----------------------------------------------------------


@pytest.mark.parametrize("value", ["20:00", "07:30", "0:05", " 23:59 "])
def test_reminder_time_accepts_valid_times(value):
    hour, minute = Settings(reminder_time=value).reminder_hour_minute
    assert 0 <= hour <= 23 and 0 <= minute <= 59


@pytest.mark.parametrize("value", ["24:00", "20:60", "8pm", "20", "20:0", "", "ab:cd", "-1:00"])
def test_reminder_time_rejects_bad_values(value):
    with pytest.raises(ValueError, match="REMINDER_TIME"):
        Settings(reminder_time=value)
