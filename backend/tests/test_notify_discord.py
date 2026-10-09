"""Discord reminders and sending to several channels (services/notify.py, v5).

Discord and ntfy are both faked with respx routes, so nothing real is ever sent.
The webhook URL below is fake; tests also check that it never leaks into logs or errors.
"""

import json

import httpx
import pytest
from loguru import logger
from pydantic import ValidationError

from config import Settings, settings
from services import notify

SECRET = "fake-token-SECRET"
WEBHOOK = f"https://discord.com/api/webhooks/123/{SECRET}"
NTFY_URL = "https://ntfy.example.test/my-secret-topic"


@pytest.fixture
def logs():
    """Collect log messages written with loguru."""
    messages = []
    handler_id = logger.add(lambda message: messages.append(str(message)), level="INFO")
    yield messages
    logger.remove(handler_id)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Record 429 waits instead of really sleeping."""
    waits = []
    monkeypatch.setattr(notify.time, "sleep", waits.append)
    return waits


@pytest.fixture
def discord(fake_leetcode, monkeypatch):
    """Turn Discord on with a fake webhook. Returns the respx route."""
    monkeypatch.setattr(settings, "discord_webhook_url", WEBHOOK)
    monkeypatch.setattr(settings, "discord_user_id", "")
    return fake_leetcode.router.post(WEBHOOK).mock(return_value=httpx.Response(200, json={}))


@pytest.fixture
def ntfy(fake_leetcode, monkeypatch):
    monkeypatch.setattr(settings, "ntfy_server", "https://ntfy.example.test")
    monkeypatch.setattr(settings, "ntfy_topic", "my-secret-topic")
    return fake_leetcode.router.post(NTFY_URL).mock(return_value=httpx.Response(200))


def body(route, index=-1) -> dict:
    return json.loads(route.calls[index].request.content)


# --- Discord request shape ---------------------------------------------------


def test_discord_only_without_user_id(discord):
    assert notify.send("LeetCode reminder", "Solve one!") is True

    assert discord.call_count == 1
    request = discord.calls.last.request
    assert request.url.params["wait"] == "true"
    assert body(discord) == {
        "content": "**LeetCode reminder**\nSolve one!",
        "username": "LeetCode Tracker",
        "allowed_mentions": {"parse": []},
    }


def test_discord_with_user_id_mentions_only_that_user(discord, monkeypatch):
    monkeypatch.setattr(settings, "discord_user_id", "111222333")

    notify.send("LeetCode reminder", "Solve one!")

    sent = body(discord)
    assert sent["content"] == "<@111222333> **LeetCode reminder**\nSolve one!"
    assert sent["allowed_mentions"] == {"users": ["111222333"]}


def test_long_content_is_truncated_to_discord_limit(discord):
    notify.send("title", "x" * 5000)

    content = body(discord)["content"]
    assert len(content) <= 2000
    assert content.startswith("**title**\nxxx")


# --- Several channels ----------------------------------------------------------


def test_both_channels_are_called(discord, ntfy):
    assert notify.send("title", "message") is True
    assert discord.call_count == 1
    assert ntfy.call_count == 1


def test_one_channel_failing_still_returns_true_and_logs(discord, ntfy, logs):
    discord.mock(return_value=httpx.Response(500))

    assert notify.send("title", "message") is True

    assert ntfy.call_count == 1
    assert any("discord failed" in message for message in logs)
    assert not any(SECRET in message for message in logs)


def test_both_failing_raises_notify_error_naming_channels(discord, ntfy, logs):
    discord.mock(return_value=httpx.Response(500))
    ntfy.mock(return_value=httpx.Response(500))

    with pytest.raises(notify.NotifyError) as caught:
        notify.send("title", "message")

    assert "ntfy failed" in str(caught.value)
    assert "discord failed" in str(caught.value)
    assert SECRET not in str(caught.value)
    assert not any(SECRET in message for message in logs)


def test_discord_network_error_does_not_leak_url(discord, logs):
    discord.mock(side_effect=httpx.ConnectError(f"cannot connect to {WEBHOOK}"))

    with pytest.raises(notify.NotifyError) as caught:
        notify.send("title", "message")

    assert SECRET not in str(caught.value)
    assert caught.value.__cause__ is None
    assert not any(SECRET in message for message in logs)


# --- Rate limits (HTTP 429) ----------------------------------------------------


def test_429_then_success_retries_once(discord, no_sleep):
    discord.side_effect = [
        httpx.Response(429, json={"retry_after": 0.25}),
        httpx.Response(200, json={}),
    ]

    assert notify.send("title", "message") is True

    assert discord.call_count == 2
    assert no_sleep == [0.25]


def test_429_twice_is_a_failure(discord, no_sleep):
    discord.side_effect = [
        httpx.Response(429, json={"retry_after": 60}),
        httpx.Response(429, json={"retry_after": 60}),
    ]

    with pytest.raises(notify.NotifyError, match="discord failed"):
        notify.send("title", "message")

    assert discord.call_count == 2
    assert no_sleep == [5.0]  # capped at 5 seconds


# --- Config validation ---------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        f"https://example.com/api/webhooks/123/{SECRET}",
        f"http://discord.com/api/webhooks/123/{SECRET}",
        f"https://discord.com/api/other/{SECRET}",
    ],
)
def test_invalid_webhook_url_fails_without_showing_it(url):
    with pytest.raises(ValidationError) as caught:
        Settings(discord_webhook_url=url)

    assert "DISCORD_WEBHOOK_URL" in str(caught.value)
    assert SECRET not in str(caught.value)


@pytest.mark.parametrize(
    "url",
    [WEBHOOK, f"https://discordapp.com/api/webhooks/123/{SECRET}", ""],
)
def test_valid_webhook_urls_are_accepted(url):
    assert Settings(discord_webhook_url=url).discord_webhook_url == url


def test_webhook_url_is_not_in_settings_repr():
    assert SECRET not in repr(Settings(discord_webhook_url=WEBHOOK))


@pytest.mark.parametrize("user_id", ["abc", "12a4", "<@123>"])
def test_user_id_must_be_digits(user_id):
    with pytest.raises(ValidationError, match="DISCORD_USER_ID"):
        Settings(discord_user_id=user_id)


# --- /api/notify/test ----------------------------------------------------------


def test_notify_test_endpoint_400_message(client):
    response = client.post("/api/notify/test")
    assert response.status_code == 400
    assert response.json()["detail"] == "Set NTFY_TOPIC or DISCORD_WEBHOOK_URL in .env"


def test_notify_test_endpoint_works_with_discord_only(client, discord):
    assert client.post("/api/notify/test").status_code == 200
    assert discord.call_count == 1
