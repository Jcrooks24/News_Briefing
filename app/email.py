import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import resend
from app import config

log = logging.getLogger(__name__)


def send_magic_link(to_email: str, name: str, token: str) -> None:
    verify_url = f"{config.BASE_URL}/auth/verify?token={token}"
    subject = "Your Morning Briefing login link"
    body_text = (
        f"Hey {name},\n\n"
        f"Click the link below to log in to Morning Briefing. "
        f"It expires in 15 minutes.\n\n"
        f"{verify_url}\n\n"
        f"If you didn't request this, you can ignore it.\n"
    )
    body_html = f"""
    <p>Hey {name},</p>
    <p>Click the button below to log in to Morning Briefing.
       This link expires in <strong>15 minutes</strong>.</p>
    <p><a href="{verify_url}" style="
         display:inline-block;
         padding:12px 24px;
         background:#1a1a1a;
         color:#fff;
         text-decoration:none;
         border-radius:6px;
         font-family:sans-serif;
    ">Log in →</a></p>
    <p style="color:#888;font-size:12px;">
      If you didn't request this, you can safely ignore this email.
    </p>
    """
    _send(to_email, subject, body_text, body_html)


def _send(to: str, subject: str, body_text: str, body_html: str) -> None:
    if config.RESEND_API_KEY:
        _send_resend(to, subject, body_text, body_html)
    elif config.SMTP_HOST:
        _send_smtp(to, subject, body_text, body_html)
    else:
        # Dev fallback — just log the link so you can click it locally
        log.warning("No email transport configured. Magic link for %s:\n%s", to, body_text)


def _send_resend(to: str, subject: str, body_text: str, body_html: str) -> None:
    resend.api_key = config.RESEND_API_KEY
    resend.Emails.send({
        "from": config.FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "text": body_text,
        "html": body_html,
    })
    log.info("Magic link email sent via Resend to %s", to)


def _send_smtp(to: str, subject: str, body_text: str, body_html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as s:
        s.ehlo()
        s.starttls()
        s.login(config.SMTP_USER, config.SMTP_PASS)
        s.sendmail(config.FROM_EMAIL, [to], msg.as_string())
    log.info("Magic link email sent via SMTP to %s", to)
