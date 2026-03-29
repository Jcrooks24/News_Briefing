from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.models import User

router = APIRouter()


@router.get("/audio/{token}")
async def get_audio(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.audio_token == token, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404)

    mp3_path = config.AUDIO_DIR / user.audio_token / "latest.mp3"
    if not mp3_path.exists():
        raise HTTPException(status_code=404, detail="No briefing has been generated yet.")

    return FileResponse(
        path=mp3_path,
        media_type="audio/mpeg",
        filename="morning_briefing.mp3",
        headers={"Cache-Control": "no-store"},
    )
