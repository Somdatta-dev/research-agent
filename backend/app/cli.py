from __future__ import annotations

import asyncio

import typer

from app.core.logging import configure_logging, get_logger

app = typer.Typer(help="Market Insights CLI")
log = get_logger(__name__)


@app.command()
def smoke() -> None:
    """Run a minimal end-to-end smoke test."""
    configure_logging("INFO")
    log.info("cli.smoke", note="use: market-insights run --config-id <uuid>")


@app.command()
def run(config_id: str = typer.Option(..., "--config-id")) -> None:
    """Run a report config end-to-end from the CLI."""
    configure_logging("INFO")
    asyncio.run(_run_cli(config_id))


async def _run_cli(config_id: str) -> None:
    from uuid import UUID

    from app.agent.runner import execute_run, setup_checkpointer, teardown_checkpointer
    from app.db.session import AsyncSessionLocal
    from app.models.run import RunTrigger
    from app.services import config_service, run_service

    await setup_checkpointer()

    try:
        async with AsyncSessionLocal() as session:
            cfg = await config_service.get_config(session, UUID(config_id))
            if cfg is None:
                log.error("cli.config_not_found", config_id=config_id)
                raise typer.Exit(1)

            run = await run_service.create_run(session, UUID(config_id), RunTrigger.MANUAL)
            log.info("cli.run.created", run_id=str(run.id), config=cfg.name)

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

        await execute_run(str(run.id), config_snapshot)
        log.info("cli.run.done", run_id=str(run.id))

    finally:
        await teardown_checkpointer()


if __name__ == "__main__":
    app()
