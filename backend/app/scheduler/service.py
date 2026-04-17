from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.timezone)


async def start_scheduler() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.config_service import list_configs

    async with AsyncSessionLocal() as session:
        configs = await list_configs(session, active=True)

    for cfg in configs:
        add_job_for_config(cfg)

    scheduler.start()
    log.info("scheduler.started", jobs=len(scheduler.get_jobs()))


def add_job_for_config(cfg) -> None:
    from app.scheduler.jobs import scheduled_run

    job_id = f"config_{cfg.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not cfg.active:
        return

    parts = cfg.schedule_cron.strip().split()
    if len(parts) != 5:
        log.warning("scheduler.bad_cron", config_id=str(cfg.id), cron=cfg.schedule_cron)
        return

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone=cfg.timezone or settings.timezone,
    )

    scheduler.add_job(
        scheduled_run,
        trigger=trigger,
        id=job_id,
        args=[str(cfg.id)],
        replace_existing=True,
    )
    log.info("scheduler.job_added", config_id=str(cfg.id), cron=cfg.schedule_cron)


def remove_job_for_config(config_id: str) -> None:
    job_id = f"config_{config_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        log.info("scheduler.job_removed", config_id=config_id)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    log.info("scheduler.stopped")
