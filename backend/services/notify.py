"""Phone notifications through ntfy (https://ntfy.sh).

ntfy is a simple push service: POST a message to {server}/{topic} and every
phone subscribed to that topic gets it. Topics on ntfy.sh are public, so pick a
long, hard-to-guess topic name.
"""

import httpx
from loguru import logger

from config import settings

TIMEOUT_SECONDS = 10


class NotifyError(Exception):
    """ntfy couldn't be reached or refused the message."""


def send(title: str, message: str) -> bool:
    """Send a notification. Returns False (and sends nothing) if NTFY_TOPIC is empty."""
    if not settings.ntfy_topic:
        logger.info("NTFY_TOPIC is not set; skipping notification {!r}", title)
        return False

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
        raise NotifyError(f"could not send notification: {error}") from error
    logger.info("Sent notification {!r}", title)
    return True
