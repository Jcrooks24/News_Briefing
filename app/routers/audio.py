from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

router = APIRouter()


@router.get("/audio/{token}")
async def get_audio(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.audio_token == token, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404)

    if not user.latest_audio:
        raise HTTPException(status_code=404, detail="No briefing has been generated yet.")

    return Response(
        content=user.latest_audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=morning_briefing.mp3",
            "Cache-Control": "no-store",
        },
    )
