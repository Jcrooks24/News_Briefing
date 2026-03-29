import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, String, Text, ForeignKey
from app.database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    email               = Column(String, nullable=False, unique=True)
    name                = Column(String, nullable=False)
    audio_token         = Column(String, nullable=False, unique=True, default=_new_uuid)
    anthropic_key_enc   = Column(LargeBinary, nullable=False)
    elevenlabs_key_enc  = Column(LargeBinary, nullable=False)
    elevenlabs_voice_id = Column(String, nullable=False)
    briefing_hour       = Column(Integer, nullable=False)
    briefing_minute     = Column(Integer, nullable=False, default=0)
    timezone            = Column(String, nullable=False, default="America/New_York")
    is_active           = Column(Boolean, nullable=False, default=False)
    created_at          = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login_at       = Column(DateTime, nullable=True)


class MagicLink(Base):
    __tablename__ = "magic_links"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash  = Column(String, nullable=False, unique=True)
    expires_at  = Column(DateTime, nullable=False)
    used        = Column(Boolean, nullable=False, default=False)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)


class BriefingRun(Base):
    __tablename__ = "briefing_runs"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at    = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at   = Column(DateTime, nullable=True)
    status        = Column(String, nullable=False, default="running")  # running | success | error
    is_wildcard   = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    mp3_bytes     = Column(Integer, nullable=True)
