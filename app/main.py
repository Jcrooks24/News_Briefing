import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.database import Base, engine, SessionLocal
from app import scheduler as sched
from app.routers import auth, account, audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables
    Base.metadata.create_all(bind=engine)
    # Start scheduler and load existing users
    sched.scheduler.start()
    db = SessionLocal()
    try:
        sched.load_all_users(db)
    finally:
        db.close()
    yield
    sched.scheduler.shutdown(wait=False)


app = FastAPI(title="Morning Briefing", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="briefing_session",
    max_age=60 * 60 * 24 * 30,  # 30 days
    https_only=False,  # set True in prod behind Railway's TLS termination
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(account.router)
app.include_router(audio.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
