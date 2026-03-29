import logging
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.models import User
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


def load_all_users(db: Session) -> None:
    """Called at startup to register jobs for every active user."""
    users = db.query(User).filter(User.is_active == True).all()
    for user in users:
        schedule_user(user)
    log.info("Loaded %d user schedule(s)", len(users))
