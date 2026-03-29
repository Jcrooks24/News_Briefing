from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.storage import audio_exists, download_audio

router = APIRouter()


@router.get("/audio/{token}")
async def get_audio(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.audio_token == token, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404)

    if not audio_exists(user.audio_token):
        raise HTTPException(status_code=404, detail="No briefing has been generated yet.")

    audio_bytes = download_audio(user.audio_token)
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=morning_briefing.mp3",
            "Cache-Control": "no-store",
        },
    )
