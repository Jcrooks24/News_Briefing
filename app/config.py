import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SECRET_KEY: str = os.environ["SECRET_KEY"]
DATABASE_URL: str = os.environ["DATABASE_URL"]
BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")

# Email — supports Resend API or SMTP
RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")
FROM_EMAIL: str = os.getenv("FROM_EMAIL", "briefings@example.com")

