"""Background jobs: sync every few hours, and an evening reminder.

Uses APScheduler's BackgroundScheduler, which runs jobs in a thread inside the
FastAPI process. Started from main.py only when ENABLE_SCHEDULER=true.
Each job opens its own DB session and catches every exception, because a
failing job must never crash the app.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlmodel import Session

import db
from config import settings
from services import notify
from services.clock import today_local
from services.stats import get_stats
from services.sync import SyncResult, sync_and_record

REMINDER_TITLE = "LeetCode reminder"


def scheduled_sync() -> SyncResult | None:
    """Job 1: sync from LeetCode. Returns None if it failed or was skipped."""
    if not settings.leetcode_username:
        logger.warning("Scheduled sync skipped: LEETCODE_USERNAME is not set")
        return None
    try:
        with Session(db.engine) as session:
            result = sync_and_record(session, settings.leetcode_username)
    except Exception:  # any failure is logged, never raised
        logger.exception("Scheduled sync failed")
        return None
    logger.info("Scheduled sync: added {}, skipped {}", result.added, result.skipped)
    return result


def reminder_message(streak: int) -> str:
    if streak > 0:
        return f"No LeetCode yet today. 🔥 {streak}-day streak at risk."
    return "No LeetCode yet today. Solve one to start a streak."


def evening_reminder() -> bool:
    """Job 2: sync, then notify if today still isn't done. Returns True if it notified."""
    scheduled_sync()  # maybe you solved one since the last sync
    try:
        with Session(db.engine) as session:
            stats = get_stats(session, today_local())
        if stats.today_done:
            logger.info("Reminder not needed: today is done")
            return False
        return notify.send(REMINDER_TITLE, reminder_message(stats.current_streak))
    except Exception:
        logger.exception("Evening reminder failed")
        return False


def build_scheduler() -> BackgroundScheduler:
    """Create (but don't start) the scheduler with both jobs, in the configured TZ."""
    scheduler = BackgroundScheduler(timezone=settings.zone)
    scheduler.add_job(
        scheduled_sync,
        IntervalTrigger(hours=settings.sync_interval_hours, timezone=settings.zone),
        id="sync",
    )
    hour, minute = settings.reminder_hour_minute
    scheduler.add_job(
        evening_reminder,
        CronTrigger(hour=hour, minute=minute, timezone=settings.zone),
        id="reminder",
    )
    return scheduler
