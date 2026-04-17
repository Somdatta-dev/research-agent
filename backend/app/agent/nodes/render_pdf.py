from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langgraph.config import get_stream_writer
from weasyprint import HTML

from app.agent.state import ReportState
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_jinja = Environment(
    loader=FileSystemLoader("app/pdf/templates"),
    autoescape=select_autoescape(["html"]),
)


async def render_pdf_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    run_id = state["run_id"]
    config = state["config"]

    template_name = config.get("pdf_template", "linkedin_carousel")
    template = _jinja.get_template(f"{template_name}.html")

    html_content = template.render(
        cover_blurb=state.get("cover_blurb", ""),
        sections=state.get("sections", []),
        draft_markdown=state.get("draft_markdown", ""),
        config_name=config.get("name", "Market Insights"),
        topic=config.get("topic", ""),
    )

    out_dir = Path(settings.reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{run_id}.pdf"

    writer({"type": "log", "message": "rendering PDF"})
    HTML(string=html_content).write_pdf(str(pdf_path))

    page_count = _count_pages(pdf_path)
    writer({"type": "pdf_rendered", "path": str(pdf_path), "pages": page_count})
    log.info("render.done", path=str(pdf_path), pages=page_count)
    return {"pdf_path": str(pdf_path)}


def _count_pages(path: Path) -> int:
    try:
        data = path.read_bytes()
        return data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    except Exception:
        return 0
