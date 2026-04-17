from __future__ import annotations

import json

from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

from app.adapters.llm import resolve_llm
from app.adapters.search import TavilySearchAdapter
from app.agent.state import EnrichInput, EnrichedHit
from app.core.logging import get_logger
from app.schemas.llm_config import LLMConfig

log = get_logger(__name__)


async def enrich_one_node(state: EnrichInput) -> dict:
    writer = get_stream_writer()
    hit = state["hit"]
    config = state["config"]
    llm_config = LLMConfig.model_validate(config.get("llm_config") or {})

    writer({"type": "enrichment_start", "url": hit["url"], "title": hit["title"]})

    full_text = ""
    try:
        tavily = TavilySearchAdapter()
        extracts = await tavily.extract([hit["url"]])
        if extracts:
            full_text = extracts[0].get("raw_content", "")[:8000]
    except Exception as exc:
        log.warning("enrich.extract_failed", url=hit["url"], error=str(exc))
        full_text = hit.get("snippet", "")

    if not full_text:
        full_text = hit.get("snippet", "")

    prompt = (
        f"Analyze this article and return JSON with: "
        f'{{"summary": "...", "key_points": ["..."], "entities": ["..."]}}\n\n'
        f"Title: {hit['title']}\n"
        f"URL: {hit['url']}\n\n"
        f"{full_text[:6000]}"
    )

    llm = resolve_llm("fast", llm_config, tags=["enrich"])
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
    except json.JSONDecodeError:
        parsed = {"summary": text[:500], "key_points": [], "entities": []}

    enriched = EnrichedHit(
        url=hit["url"],
        title=hit["title"],
        full_text=full_text[:4000],
        summary=parsed.get("summary", ""),
        key_points=parsed.get("key_points", []),
        entities=parsed.get("entities", []),
    )

    writer({"type": "enrichment_done", "url": hit["url"]})
    log.info("enrich.done", url=hit["url"])
    return {"enriched_hits": [enriched]}
