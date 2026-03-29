from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import create_magic_link, verify_magic_link
from app.database import get_db
from app.email import send_magic_link
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/auth/magic-link")
async def request_magic_link(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if user and user.is_active:
        token = create_magic_link(user, db)
        send_magic_link(user.email, user.name, token)
    return templates.TemplateResponse(request, "verify_sent.html")


@router.get("/auth/verify", response_class=HTMLResponse)
async def verify(token: str, request: Request, db: Session = Depends(get_db)):
    user = verify_magic_link(token, db)
    if not user:
        return templates.TemplateResponse(
            request, "error.html",
            {"message": "This link has expired or already been used. Please request a new one."},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/account", status_code=303)


@router.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
