import uuid
import pytz
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.crypto import encrypt
from app.database import get_db
from app.models import User
from app.auth import create_magic_link
from app.email import send_magic_link
from app import config, scheduler as sched

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ALL_TIMEZONES = sorted(pytz.all_timezones)


def _current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"timezones": ALL_TIMEZONES})


@router.get("/setup-guide", response_class=HTMLResponse)
async def setup_guide(request: Request):
    return templates.TemplateResponse(request, "setup_guide.html")


@router.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    anthropic_key: str = Form(...),
    elevenlabs_key: str = Form(...),
    elevenlabs_voice_id: str = Form(...),
    briefing_time: str = Form(...),
    timezone: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.lower().strip()

    if timezone not in pytz.all_timezones:
        return templates.TemplateResponse(
            request, "signup.html",
            {"timezones": ALL_TIMEZONES, "error": "Invalid timezone selected."},
            status_code=400,
        )

    try:
        hour, minute = [int(x) for x in briefing_time.split(":")]
    except ValueError:
        return templates.TemplateResponse(
            request, "signup.html",
            {"timezones": ALL_TIMEZONES, "error": "Invalid time format."},
            status_code=400,
        )

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        token = create_magic_link(existing, db)
        send_magic_link(existing.email, existing.name, token)
        return templates.TemplateResponse(
            request, "verify_sent.html",
            {"message": "That email is already registered. We sent you a login link."},
        )

    user = User(
        email=email,
        name=name.strip(),
        anthropic_key_enc=encrypt(anthropic_key.strip()),
        elevenlabs_key_enc=encrypt(elevenlabs_key.strip()),
        elevenlabs_voice_id=elevenlabs_voice_id.strip(),
        briefing_hour=hour,
        briefing_minute=minute,
        timezone=timezone,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_magic_link(user, db)
    send_magic_link(user.email, user.name, token)
    return templates.TemplateResponse(request, "verify_sent.html")


# ---------------------------------------------------------------------------
# Account settings (requires login)
# ---------------------------------------------------------------------------

@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    audio_url = f"{config.BASE_URL}/audio/{user.audio_token}"
    return templates.TemplateResponse(
        request, "account.html",
        {"user": user, "timezones": ALL_TIMEZONES, "audio_url": audio_url},
    )


@router.post("/account/update")
async def account_update(
    request: Request,
    name: str = Form(...),
    anthropic_key: str = Form(""),
    elevenlabs_key: str = Form(""),
    elevenlabs_voice_id: str = Form(...),
    briefing_time: str = Form(...),
    timezone: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if timezone not in pytz.all_timezones:
        return RedirectResponse("/account?error=timezone", status_code=303)

    try:
        hour, minute = [int(x) for x in briefing_time.split(":")]
    except ValueError:
        return RedirectResponse("/account?error=time", status_code=303)

    user.name = name.strip()
    user.elevenlabs_voice_id = elevenlabs_voice_id.strip()
    user.briefing_hour = hour
    user.briefing_minute = minute
    user.timezone = timezone

    if anthropic_key.strip():
        user.anthropic_key_enc = encrypt(anthropic_key.strip())
    if elevenlabs_key.strip():
        user.elevenlabs_key_enc = encrypt(elevenlabs_key.strip())

    db.commit()
    sched.schedule_user(user)
    return RedirectResponse("/account?saved=1", status_code=303)


@router.post("/account/rotate-token")
async def rotate_token(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    user.audio_token = str(uuid.uuid4())
    db.commit()
    return RedirectResponse("/account?saved=1", status_code=303)


@router.post("/account/test-briefing")
async def test_briefing(request: Request, db: Session = Depends(get_db)):
    """Trigger an immediate briefing generation for the logged-in user."""
    import asyncio
    from app.briefing.runner import run_for_user
    user = _current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    asyncio.get_event_loop().run_in_executor(None, run_for_user, user.id)
    return RedirectResponse("/account?generating=1", status_code=303)
