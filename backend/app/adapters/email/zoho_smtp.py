from __future__ import annotations

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30), reraise=True)
async def send_email(
    *,
    to_addresses: list[str],
    subject: str,
    body_html: str,
    attachment_path: Path | None = None,
) -> dict:
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject

    msg.attach(MIMEText(body_html, "html", "utf-8"))

    if attachment_path and attachment_path.exists():
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=attachment_path.name)
        part["Content-Disposition"] = f'attachment; filename="{attachment_path.name}"'
        msg.attach(part)

    kwargs: dict = {
        "hostname": settings.smtp_host,
        "port": settings.smtp_port,
        "username": settings.smtp_username,
        "password": settings.smtp_password,
    }
    if settings.smtp_use_ssl:
        kwargs["use_tls"] = True
    else:
        kwargs["start_tls"] = True

    result = await aiosmtplib.send(msg, **kwargs)

    log.info(
        "email.sent",
        to=to_addresses,
        subject=subject,
        attachment=str(attachment_path) if attachment_path else None,
    )
    return {"sent": True, "to": to_addresses, "response": str(result)}
