from __future__ import annotations

from langgraph.config import get_stream_writer

from app.agent.state import ReportState, SearchHit
from app.core.logging import get_logger
from app.services.coverage_service import filter_and_record

log = get_logger(__name__)


async def dedup_node(state: ReportState) -> dict:
    writer = get_stream_writer()
    config = state["config"]
    raw_hits = state.get("raw_hits", [])

    kept = await filter_and_record(
        config_id=config["id"],
        run_id=state["run_id"],
        hits=raw_hits,
        window_days=config.get("dedup_window_days", 7),
    )

    rejected = len(raw_hits) - len(kept)
    writer({
        "type": "dedup_summary",
        "in": len(raw_hits),
        "kept": len(kept),
        "rejected": rejected,
    })
    log.info("dedup.done", raw=len(raw_hits), kept=len(kept), rejected=rejected)

    return {"deduped_hits": kept}
