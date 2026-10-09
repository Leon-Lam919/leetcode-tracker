"""Reminders to your phone, through ntfy and/or a Discord webhook.

Every configured channel gets every message:

- ntfy (https://ntfy.sh): POST the text to {server}/{topic} and every phone
  subscribed to that topic gets it. Topics on ntfy.sh are public, so pick a
  long, hard-to-guess topic name.
- Discord: POST JSON to a channel webhook URL. The URL is a secret (anyone who
  has it can post to the channel), so it never appears in logs or errors.

send() returns False when no channel is configured, True when at least one
channel worked, and raises NotifyError only when every configured channel failed.
"""

import time

import httpx
from loguru import logger

from config import settings

TIMEOUT_SECONDS = 10
DISCORD_USERNAME = "LeetCode Tracker"
DISCORD_MAX_CONTENT = 2000  # Discord rejects longer message content
DISCORD_MAX_RETRY_AFTER = 5.0  # seconds; never wait longer than this on a 429


class NotifyError(Exception):
    """Every configured channel failed to deliver the message."""


class ChannelError(Exception):
    """One channel failed. The message is safe to log: it never contains a URL."""


def send(title: str, message: str) -> bool:
    """Send to every configured channel. Returns False (and sends nothing) if none is set."""
    channels = configured_channels()
    if not channels:
        logger.info(
            "NTFY_TOPIC is not set and DISCORD_WEBHOOK_URL is not set; skipping notification {!r}",
            title,
        )
        return False

    failures = []
    for name in channels:
        try:
            SENDERS[name](title, message)
        except ChannelError as error:
            logger.warning("Notification channel {} failed: {}", name, error)
            failures.append(f"{name} failed: {error}")
        else:
            logger.info("Sent notification {!r} via {}", title, name)

    if len(failures) == len(channels):
        raise NotifyError("; ".join(failures))
    return True


def configured_channels() -> list[str]:
    """Names of the channels that are switched on, e.g. ["ntfy", "discord"]."""
    channels = []
    if settings.ntfy_topic:
        channels.append("ntfy")
    if settings.discord_webhook_url:
        channels.append("discord")
    return channels


def _send_ntfy(title: str, message: str) -> None:
    url = f"{settings.ntfy_server.rstrip('/')}/{settings.ntfy_topic}"
    try:
        response = httpx.post(
            url,
            content=message.encode(),  # the body is the message text (UTF-8, emoji are fine)
            headers={"Title": title},  # header values must be plain ASCII
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise ChannelError(f"could not send notification: {error}") from error


def discord_payload(title: str, message: str) -> dict:
    """The webhook JSON body. Only the configured user (if any) can be pinged."""
    user_id = settings.discord_user_id
    if user_id:
        content = f"<@{user_id}> **{title}**\n{message}"
        allowed_mentions = {"users": [user_id]}
    else:
        content = f"**{title}**\n{message}"
        allowed_mentions = {"parse": []}  # nothing in the text can ping anyone
    if len(content) > DISCORD_MAX_CONTENT:
        content = content[: DISCORD_MAX_CONTENT - 1] + "…"
    return {
        "content": content,
        "username": DISCORD_USERNAME,
        "allowed_mentions": allowed_mentions,
    }


def _send_discord(title: str, message: str) -> None:
    """POST to the webhook, retrying once after a 429. Errors never include the URL."""
    payload = discord_payload(title, message)
    response = _post_discord(payload)
    if response.status_code == 429:
        wait = _retry_after_seconds(response)
        logger.info("Discord rate limit hit; retrying once in {:.1f}s", wait)
        time.sleep(wait)
        response = _post_discord(payload)
    if not response.is_success:
        raise ChannelError(f"Discord answered HTTP {response.status_code}")


def _post_discord(payload: dict) -> httpx.Response:
    try:
        return httpx.post(
            settings.discord_webhook_url,
            params={"wait": "true"},  # Discord confirms the message was posted
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as error:
        # str(error) can contain the request URL, so only the error type is kept.
        raise ChannelError(f"could not reach Discord ({type(error).__name__})") from None


def _retry_after_seconds(response: httpx.Response) -> float:
    """Discord's 429 body says how long to wait. Capped, and 1s if it's missing."""
    try:
        seconds = float(response.json().get("retry_after", 1))
    except (ValueError, AttributeError, TypeError):
        seconds = 1.0
    return max(0.0, min(seconds, DISCORD_MAX_RETRY_AFTER))


SENDERS = {"ntfy": _send_ntfy, "discord": _send_discord}
