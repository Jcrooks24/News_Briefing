import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import MagicLink, User


MAGIC_LINK_EXPIRY_MINUTES = 15


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_magic_link(user: User, db: Session) -> str:
    """Generate a magic link token, store its hash, and return the raw token."""
    raw = secrets.token_urlsafe(32)
    link = MagicLink(
        user_id=user.id,
        token_hash=_hash_token(raw),
        expires_at=datetime.utcnow() + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES),
    )
    db.add(link)
    db.commit()
    return raw


def verify_magic_link(raw_token: str, db: Session) -> User | None:
    """
    Validate a magic link token. Returns the User on success, None otherwise.
    Marks the link as used so it cannot be reused.
    """
    token_hash = _hash_token(raw_token)
    link = db.query(MagicLink).filter(
        MagicLink.token_hash == token_hash,
        MagicLink.used == False,
        MagicLink.expires_at > datetime.utcnow(),
    ).first()

    if not link:
        return None

    link.used = True
    user = db.query(User).filter(User.id == link.user_id).first()
    if user:
        user.is_active = True
        user.last_login_at = datetime.utcnow()
    db.commit()
    return user
