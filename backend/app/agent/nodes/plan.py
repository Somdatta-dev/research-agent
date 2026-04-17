from __future__ import annotations

import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

from app.adapters.llm import resolve_llm
from app.agent.state import ReportState
from app.core.logging import get_logger
from app.schemas.llm_config import LLMConfig
from app.services.coverage_service import get_recent_titles

log = get_logger(__name__)

_jinja = Environment(
    loader=FileSystemLoader("app/agent/prompts"),
    autoescape=select_autoescape([]),
)


async def plan_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    config = state["config"]
    llm_config = LLMConfig.model_validate(config.get("llm_config") or {})

    recent_titles = await get_recent_titles(
        config_id=config["id"],
        days=config.get("dedup_window_days", 7),
    )

    template = _jinja.get_template("plan.j2")
    prompt = template.render(
        topic=config["topic"],
        focus_areas=config.get("focus_areas", []),
        recent_titles=recent_titles,
        dedup_window_days=config.get("dedup_window_days", 7),
    )

    writer({"type": "log", "message": "generating research plan"})

    llm = resolve_llm("fast", llm_config, tags=["plan"])
    resp = await llm.ainvoke([HumanMessage(content=prompt)])

    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    plan = json.loads(text)
    writer({"type": "plan_ready", "subtopics": len(plan)})
    log.info("plan.done", subtopics=len(plan))
    return {"plan": plan}
