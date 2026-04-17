from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.adapters.search.base import ExtractResult, SearchAdapter, SearchResult
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"


class TavilySearchAdapter(SearchAdapter):
    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self._api_key = api_key or settings.tavily_api_key
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
            resp = await client.post(
                TAVILY_SEARCH_URL,
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "include_raw_content": False,
                    "days": recency_days,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results: list[SearchResult] = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    published_at=item.get("published_date"),
                    source="tavily",
                    score=item.get("score", 0.0),
                )
            )
        log.info("tavily.search", query=query, hits=len(results))
        return results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def extract(self, urls: list[str]) -> list[ExtractResult]:
        if not urls:
            return []
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                TAVILY_EXTRACT_URL,
                json={"api_key": self._api_key, "urls": urls},
            )
            resp.raise_for_status()
            data = resp.json()

        results: list[ExtractResult] = []
        for item in data.get("results", []):
            results.append(
                ExtractResult(
                    url=item.get("url", ""),
                    raw_content=item.get("raw_content", ""),
                )
            )
        log.info("tavily.extract", urls=len(urls), extracted=len(results))
        return results
