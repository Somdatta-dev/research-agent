from __future__ import annotations

from uuid import UUID

from app.agent.runner import execute_run
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.run import RunTrigger
from app.services import config_service, run_service

log = get_logger(__name__)


async def scheduled_run(config_id: str) -> None:
    async with AsyncSessionLocal() as session:
        cfg = await config_service.get_config(session, UUID(config_id))
        if not cfg or not cfg.active:
            log.info("scheduler.skip", config_id=config_id, reason="inactive or missing")
            return

        run = await run_service.create_run(session, UUID(config_id), RunTrigger.SCHEDULED)

        config_snapshot = {
            "id": str(cfg.id),
            "name": cfg.name,
            "topic": cfg.topic,
            "focus_areas": cfg.focus_areas or [],
            "schedule_cron": cfg.schedule_cron,
            "timezone": cfg.timezone,
            "recipients": cfg.recipients or [],
            "search_config": cfg.search_config or {},
            "llm_config": cfg.llm_config or {},
            "dedup_window_days": cfg.dedup_window_days,
            "pdf_template": cfg.pdf_template,
            "max_pages": cfg.max_pages,
        }

    log.info("scheduler.run_started", run_id=str(run.id), config=cfg.name)
    await execute_run(str(run.id), config_snapshot)
