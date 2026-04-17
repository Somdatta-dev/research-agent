from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.runner import setup_checkpointer, teardown_checkpointer
from app.api.routes import configs, health, reports, runs, ws
from app.core.config import settings
from app.core.events import close_redis
from app.core.logging import configure_logging, get_logger
from app.scheduler.service import start_scheduler, stop_scheduler
from app.seed.loader import seed_configs_if_empty

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    log.info("api.start", env=settings.app_env, port=settings.api_port)
    try:
        await setup_checkpointer()
    except Exception as exc:
        log.warning("checkpointer.init_failed", error=str(exc))
    try:
        await seed_configs_if_empty()
    except Exception as exc:
        log.warning("seed.failed", error=str(exc))
    try:
        await start_scheduler()
    except Exception as exc:
        log.warning("scheduler.init_failed", error=str(exc))
    yield
    try:
        stop_scheduler()
    except Exception:
        pass
    try:
        await teardown_checkpointer()
    except Exception:
        pass
    await close_redis()
    log.info("api.stop")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Market Insights API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(configs.router, prefix="/api/v1")
    app.include_router(runs.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(ws.router, prefix="/api/v1")
    return app


app = create_app()
