"""Read and write the `meta` key-value table."""

from datetime import UTC, datetime

from sqlmodel import Session

from models.tables import Meta
from services import clock

LAST_SYNC_AT = "last_sync_at"
LAST_SYNC_RESULT = "last_sync_result"


def get_value(session: Session, key: str) -> str | None:
    row = session.get(Meta, key)
    return row.value if row else None


def set_value(session: Session, key: str, value: str) -> None:
    row = session.get(Meta, key) or Meta(key=key, value=value)
    row.value = value
    session.add(row)


def record_sync(session: Session, result: str) -> None:
    """Remember when a sync ran and what happened. Commits."""
    set_value(session, LAST_SYNC_AT, clock.utc_now().isoformat())
    set_value(session, LAST_SYNC_RESULT, result)
    session.commit()


def last_sync(session: Session) -> tuple[datetime | None, str | None]:
    at = get_value(session, LAST_SYNC_AT)
    moment = datetime.fromisoformat(at).astimezone(UTC) if at else None
    return moment, get_value(session, LAST_SYNC_RESULT)
