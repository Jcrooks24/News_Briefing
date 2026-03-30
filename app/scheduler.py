import logging
import threading
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.models import User, BriefingRun
from app.briefing.runner import run_for_user

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _job_id(user_id: int) -> str:
    return f"briefing_user_{user_id}"


def schedule_user(user: User) -> None:
    """Add or replace a user's daily briefing job."""
    try:
        tz = pytz.timezone(user.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        log.error("Unknown timezone '%s' for user %d — skipping schedule", user.timezone, user.id)
        return

    scheduler.add_job(
        func=run_for_user,
        trigger=CronTrigger(hour=user.briefing_hour, minute=user.briefing_minute, timezone=tz),
        id=_job_id(user.id),
        args=[user.id],
        replace_existing=True,
    )
    log.info(
        "Scheduled user %d (%s) at %02d:%02d %s",
        user.id, user.email, user.briefing_hour, user.briefing_minute, user.timezone,
    )


def unschedule_user(user_id: int) -> None:
    job_id = _job_id(user_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        log.info("Unscheduled user %d", user_id)


def _already_ran_today(user: User, db: Session) -> bool:
    """Return True if a successful briefing run exists for today in the user's local timezone."""
    try:
        tz = pytz.timezone(user.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        return False
    now_local = datetime.now(tz)
    today_start_utc = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.utc).replace(tzinfo=None)
    return db.query(BriefingRun).filter(
        BriefingRun.user_id == user.id,
        BriefingRun.status == "success",
        BriefingRun.started_at >= today_start_utc,
    ).first() is not None


def load_all_users(db: Session) -> None:
    """Called at startup to register jobs for every active user."""
    users = db.query(User).filter(User.is_active == True).all()
    for user in users:
        schedule_user(user)
        # Catch-up: if the scheduled time already passed today but no successful run exists,
        # fire immediately. Guards against Railway process restarts killing in-memory jobs.
        try:
            tz = pytz.timezone(user.timezone)
            now_local = datetime.now(tz)
            scheduled_today = now_local.replace(
                hour=user.briefing_hour, minute=user.briefing_minute, second=0, microsecond=0
            )
            if now_local >= scheduled_today and not _already_ran_today(user, db):
                log.info("Missed briefing for user %d — running catch-up now", user.id)
                threading.Thread(target=run_for_user, args=[user.id], daemon=True).start()
        except Exception as exc:
            log.error("Error checking missed briefing for user %d: %s", user.id, exc)
    log.info("Loaded %d user schedule(s)", len(users))
