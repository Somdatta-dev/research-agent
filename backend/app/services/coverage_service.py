from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.agent.state import SearchHit
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.coverage import CoverageLog

log = get_logger(__name__)

STRIP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/")
    qs = parse_qs(parsed.query, keep_blank_values=False)
    filtered = {k: v for k, v in qs.items() if k not in STRIP_PARAMS}
    query = urlencode(filtered, doseq=True)
    return urlunparse(("https", host, path, "", query, ""))


def hash_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    tokens = sorted(t.split())
    return " ".join(tokens)


async def get_recent_titles(config_id: str, days: int = 7) -> list[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(CoverageLog.title)
            .where(
                and_(
                    CoverageLog.config_id == config_id,
                    CoverageLog.first_seen_at >= cutoff,
                    CoverageLog.title.isnot(None),
                )
            )
            .order_by(CoverageLog.first_seen_at.desc())
            .limit(50)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]


async def filter_and_record(
    config_id: str,
    run_id: str,
    hits: list[SearchHit],
    window_days: int = 7,
) -> list[SearchHit]:
    if not hits:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    async with AsyncSessionLocal() as session:
        stmt = select(CoverageLog.url_hash, CoverageLog.title_hash).where(
            and_(
                CoverageLog.config_id == config_id,
                CoverageLog.first_seen_at >= cutoff,
            )
        )
        result = await session.execute(stmt)
        existing_url_hashes = set()
        existing_title_hashes = set()
        for row in result.all():
            existing_url_hashes.add(row[0])
            if row[1]:
                existing_title_hashes.add(row[1])

    kept: list[SearchHit] = []
    seen_urls: set[str] = set()

    for hit in hits:
        norm_url = normalize_url(hit["url"])
        url_h = hash_string(norm_url)

        if url_h in seen_urls:
            continue
        seen_urls.add(url_h)

        if url_h in existing_url_hashes:
            continue

        title_h = hash_string(normalize_title(hit["title"])) if hit.get("title") else None
        if title_h and title_h in existing_title_hashes:
            continue

        kept.append(hit)

        async with AsyncSessionLocal() as session:
            insert_stmt = pg_insert(CoverageLog).values(
                config_id=config_id,
                url=hit["url"],
                url_hash=url_h,
                title=hit.get("title"),
                title_hash=title_h,
                run_ids=[run_id],
            )
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["config_id", "url_hash"],
                set_={
                    "last_seen_at": datetime.now(timezone.utc),
                    "run_ids": CoverageLog.run_ids + [run_id],
                },
            )
            await session.execute(insert_stmt)
            await session.commit()

    log.info("coverage.filter", total=len(hits), kept=len(kept))
    return kept
