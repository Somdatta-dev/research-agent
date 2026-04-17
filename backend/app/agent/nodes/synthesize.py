from __future__ import annotations

import json
from itertools import groupby

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

from app.adapters.llm import resolve_llm
from app.agent.state import EnrichedHit, ReportState, Section
from app.core.logging import get_logger
from app.schemas.llm_config import LLMConfig

log = get_logger(__name__)

_jinja = Environment(
    loader=FileSystemLoader("app/agent/prompts"),
    autoescape=select_autoescape([]),
)


def _group_by_theme(hits: list[EnrichedHit]) -> dict[str, list[EnrichedHit]]:
    themes: dict[str, list[EnrichedHit]] = {}
    for hit in hits:
        entities = hit.get("entities", [])
        theme = entities[0] if entities else "General"
        themes.setdefault(theme, []).append(hit)

    if len(themes) > 7:
        sorted_themes = sorted(themes.items(), key=lambda x: -len(x[1]))
        themes = dict(sorted_themes[:5])
        others = [h for k, v in sorted_themes[5:] for h in v]
        if others:
            themes["Other developments"] = others

    return themes


def _parse_section(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"heading": "Section", "body_md": text, "citations": []}


async def synthesize_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    config = state["config"]
    llm_config = LLMConfig.model_validate(config.get("llm_config") or {})
    enriched = state.get("enriched_hits", [])

    themes = _group_by_theme(enriched)
    template = _jinja.get_template("synthesize.j2")
    llm = resolve_llm("primary", llm_config, tags=["synthesize"])

    sections: list[Section] = []
    for idx, (theme, hits) in enumerate(themes.items()):
        writer({"type": "synthesize_start", "theme": theme, "index": idx})

        prompt = template.render(theme=theme, hits=hits)
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        text = resp.content if isinstance(resp.content, str) else str(resp.content)

        parsed = _parse_section(text)
        section = Section(
            heading=parsed.get("heading", theme),
            body_md=parsed.get("body_md", ""),
            citations=parsed.get("citations", []),
        )
        sections.append(section)

        writer({"type": "section_drafted", "heading": section["heading"]})
        log.info("synthesize.section", theme=theme, heading=section["heading"])

    return {"sections": sections}
