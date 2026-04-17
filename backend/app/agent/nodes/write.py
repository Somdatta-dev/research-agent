from __future__ import annotations

import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

from app.adapters.llm import resolve_llm
from app.agent.state import ReportState
from app.core.logging import get_logger
from app.schemas.llm_config import LLMConfig

log = get_logger(__name__)

_jinja = Environment(
    loader=FileSystemLoader("app/agent/prompts"),
    autoescape=select_autoescape([]),
)


async def write_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    config = state["config"]
    llm_config = LLMConfig.model_validate(config.get("llm_config") or {})
    sections = state.get("sections", [])
    max_pages = config.get("max_pages", 8)

    writer({"type": "log", "message": "writing LinkedIn copy"})

    template = _jinja.get_template("write.j2")
    prompt = template.render(sections=sections, max_pages=max_pages)

    llm = resolve_llm("primary", llm_config, tags=["write"])
    resp = await llm.ainvoke([HumanMessage(content=prompt)])

    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        parsed = json.loads(text)
        cover_blurb = parsed.get("cover_blurb", "")
        draft_markdown = parsed.get("draft_markdown", text)
    except json.JSONDecodeError:
        cover_blurb = ""
        draft_markdown = text

    writer({"type": "write_done", "pages_hint": max_pages})
    log.info("write.done", cover_blurb_len=len(cover_blurb), markdown_len=len(draft_markdown))
    return {"cover_blurb": cover_blurb, "draft_markdown": draft_markdown}
