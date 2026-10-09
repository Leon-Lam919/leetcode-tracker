"""Time helpers. All "what day is it?" questions use the configured TZ."""

from datetime import UTC, date, datetime

from config import settings


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_local_date(moment: datetime) -> date:
    """Convert a UTC datetime to the calendar date in settings.tz."""
    if moment.tzinfo is None:  # SQLite gives back naive datetimes; we store them as UTC
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(settings.zone).date()


def today_local() -> date:
    return to_local_date(utc_now())
