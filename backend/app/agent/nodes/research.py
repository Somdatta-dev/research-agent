from __future__ import annotations

import asyncio

from langgraph.config import get_stream_writer

from app.adapters.search import BraveSearchAdapter, SearchResult, TavilySearchAdapter
from app.agent.state import ResearchInput
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


async def research_one_node(state: ResearchInput) -> dict:
    writer = get_stream_writer()
    subtopic = state["subtopic"]
    config = state["config"]

    queries = subtopic.get("queries", [])
    if not queries:
        return {"raw_hits": []}

    search_cfg = config.get("search_config", {})
    providers = search_cfg.get("providers", ["tavily", "brave"])
    max_results = search_cfg.get(
        "max_results_per_query", settings.search_max_results_per_query
    )
    recency = search_cfg.get(
        "recency_days", settings.search_default_recency_days
    )

    adapters = []
    if "tavily" in providers:
        adapters.append(TavilySearchAdapter())
    if "brave" in providers:
        adapters.append(BraveSearchAdapter())

    all_hits: list[SearchResult] = []

    for query in queries:
        writer({"type": "search_query", "subtopic": subtopic.get("subtopic", ""), "query": query})

        tasks = [
            adapter.search(query, max_results=max_results, recency_days=recency)
            for adapter in adapters
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, BaseException):
                log.warning("search.error", query=query, error=str(result))
                continue
            all_hits.extend(result)

        writer({"type": "search_results", "query": query, "count": sum(
            len(r) for r in results if not isinstance(r, BaseException)
        )})

    log.info(
        "research.done",
        subtopic=subtopic.get("subtopic", ""),
        total_hits=len(all_hits),
    )
    return {"raw_hits": all_hits}
