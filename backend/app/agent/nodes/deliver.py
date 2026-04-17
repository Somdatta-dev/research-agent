from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langgraph.config import get_stream_writer

from app.adapters.email import send_email
from app.agent.state import ReportState
from app.core.logging import get_logger

log = get_logger(__name__)

_jinja = Environment(
    loader=FileSystemLoader("app/pdf/templates"),
    autoescape=select_autoescape(["html"]),
)


async def deliver_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    config = state["config"]
    pdf_path_str = state.get("pdf_path")

    recipients = config.get("recipients", [])
    if not recipients:
        writer({"type": "log", "message": "no recipients configured; skipping email"})
        return {"email_result": {"sent": False, "reason": "no_recipients"}}

    to_addresses = [r["email"] for r in recipients if r.get("email")]
    if not to_addresses:
        return {"email_result": {"sent": False, "reason": "no_valid_emails"}}

    subject = f"Market Insights: {config.get('name', 'Daily Report')}"

    body_html = (
        f"<p>Your daily report for <strong>{config.get('name', '')}</strong> is attached.</p>"
        f"<p><em>{state.get('cover_blurb', '')}</em></p>"
    )

    pdf_path = Path(pdf_path_str) if pdf_path_str else None

    writer({"type": "log", "message": f"sending email to {len(to_addresses)} recipient(s)"})

    try:
        result = await send_email(
            to_addresses=to_addresses,
            subject=subject,
            body_html=body_html,
            attachment_path=pdf_path,
        )
        writer({"type": "email_sent", "to": to_addresses})
        log.info("deliver.done", to=to_addresses)
        return {"email_result": result}
    except Exception as exc:
        log.error("deliver.failed", error=str(exc))
        return {
            "email_result": {"sent": False, "error": str(exc)},
            "errors": [{"node": "deliver", "error": str(exc)}],
        }


async def soft_fail_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    config = state["config"]

    recipients = config.get("recipients", [])
    to_addresses = [r["email"] for r in recipients if r.get("email")]

    if to_addresses:
        try:
            result = await send_email(
                to_addresses=to_addresses,
                subject=f"Market Insights: No significant new developments — {config.get('name', '')}",
                body_html=(
                    f"<p>The daily research for <strong>{config.get('name', '')}</strong> "
                    f"found no significant new content that hasn't been covered recently.</p>"
                    f"<p>The agent will try again at the next scheduled run.</p>"
                ),
            )
            writer({"type": "email_sent", "to": to_addresses, "soft_fail": True})
            return {"email_result": result}
        except Exception as exc:
            log.warning("soft_fail.email_error", error=str(exc))
            return {"email_result": {"sent": False, "soft_fail": True, "error": str(exc)}}

    writer({"type": "log", "message": "soft fail — no new content, no recipients to notify"})
    return {"email_result": {"sent": False, "soft_fail": True, "reason": "no_recipients"}}
