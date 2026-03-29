"""
runner.py
---------
Orchestrates one user's full briefing pipeline:
  fetch/wildcard → Claude script → ElevenLabs TTS → save MP3
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.crypto import decrypt
from app.database import SessionLocal
from app.models import BriefingRun, User
from app.briefing.rss import fetch_all_headlines
from app.briefing.wildcard import is_wildcard_day, pick_wildcard_topic
from app.briefing.claude_client import generate_news_script, generate_wildcard_script
from app.briefing.elevenlabs_client import text_to_speech

log = logging.getLogger(__name__)



def run_for_user(user_id: int) -> None:
    """Entry point called by the scheduler. Opens its own DB session."""
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            log.warning("run_for_user: user %d not found or inactive", user_id)
            return

        run = BriefingRun(user_id=user.id, started_at=datetime.utcnow())
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            _execute(user, run, db)
        except Exception as exc:
            run.status = "error"
            run.error_message = str(exc)
            run.finished_at = datetime.utcnow()
            db.commit()
            log.error("Briefing failed for user %d (%s): %s", user.id, user.email, exc, exc_info=True)
    finally:
        db.close()


def _execute(user: User, run: BriefingRun, db: Session) -> None:
    anthropic_key   = decrypt(user.anthropic_key_enc)
    elevenlabs_key  = decrypt(user.elevenlabs_key_enc)

    # Use the user's local date for wildcard logic
    local_date = datetime.now(ZoneInfo(user.timezone)).date()

    if is_wildcard_day(local_date):
        topic = pick_wildcard_topic(local_date)
        log.info("Wildcard day for user %d — topic: %s", user.id, topic)
        script = generate_wildcard_script(
            topic=topic,
            user_name=user.name,
            api_key=anthropic_key,
        )
        run.is_wildcard = True
    else:
        headlines = fetch_all_headlines()
        if not any(headlines.values()):
            raise RuntimeError("All RSS feeds failed — nothing to brief on")
        script = generate_news_script(
            headlines=headlines,
            user_name=user.name,
            api_key=anthropic_key,
        )

    audio_bytes = text_to_speech(
        script=script,
        api_key=elevenlabs_key,
        voice_id=user.elevenlabs_voice_id,
    )

    user.latest_audio = audio_bytes
    log.info("Stored MP3 in DB (%d KB)", len(audio_bytes) // 1024)

    run.status      = "success"
    run.mp3_bytes   = len(audio_bytes)
    run.finished_at = datetime.utcnow()
    db.commit()
