from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict


class SearchResult(TypedDict):
    url: str
    title: str
    snippet: str
    published_at: str | None
    source: str
    score: float


class ExtractResult(TypedDict):
    url: str
    raw_content: str


class SearchAdapter(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        recency_days: int = 2,
    ) -> list[SearchResult]: ...

    async def extract(self, urls: list[str]) -> list[ExtractResult]:
        raise NotImplementedError
