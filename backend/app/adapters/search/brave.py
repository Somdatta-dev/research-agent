from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.adapters.search.base import SearchAdapter, SearchResult
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

FRESHNESS_MAP = {1: "pd", 2: "pw", 7: "pw", 14: "pm", 30: "pm"}


def _freshness(days: int) -> str:
    for threshold in sorted(FRESHNESS_MAP):
        if days <= threshold:
            return FRESHNESS_MAP[threshold]
    return "pm"


class BraveSearchAdapter(SearchAdapter):
    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self._api_key = api_key or settings.brave_api_key
        self._timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        recency_days: int = 2,
    ) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                BRAVE_SEARCH_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self._api_key,
                },
                params={
                    "q": query,
                    "count": max_results,
                    "freshness": _freshness(recency_days),
                    "text_decorations": "false",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results: list[SearchResult] = []
        for idx, item in enumerate(data.get("web", {}).get("results", [])):
            results.append(
                SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("description", ""),
                    published_at=item.get("page_age"),
                    source="brave",
                    score=max(1.0 - idx * 0.05, 0.1),
                )
            )
        log.info("brave.search", query=query, hits=len(results))
        return results
