from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict


class SearchHit(TypedDict):
    url: str
    title: str
    snippet: str
    published_at: str | None
    source: str
    score: float


class EnrichedHit(TypedDict):
    url: str
    title: str
    full_text: str
    summary: str
    key_points: list[str]
    entities: list[str]


class Section(TypedDict):
    heading: str
    body_md: str
    citations: list[str]


class ReportState(TypedDict):
    run_id: str
    config: dict
    plan: list[dict]
    raw_hits: Annotated[list[SearchHit], add]
    deduped_hits: list[SearchHit]
    enriched_hits: Annotated[list[EnrichedHit], add]
    sections: list[Section]
    cover_blurb: str
    draft_markdown: str
    pdf_path: str | None
    email_result: dict | None
    errors: Annotated[list[dict], add]


class ResearchInput(TypedDict):
    subtopic: dict
    config: dict


class EnrichInput(TypedDict):
    hit: SearchHit
    config: dict
