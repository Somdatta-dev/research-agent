from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.report_config import ReportConfig
from app.schemas.config import ConfigCreate
from app.services import config_service

log = get_logger(__name__)

SEED_FILE = Path(__file__).parent / "configs.json"


async def seed_configs_if_empty() -> None:
    """Seed report_configs from configs.json on first startup.
    Idempotent: only runs when the table is empty."""
    if not SEED_FILE.exists():
        log.info("seed.no_file", path=str(SEED_FILE))
        return

    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count(ReportConfig.id)))
        if count and count > 0:
            log.info("seed.skip", existing=count)
            return

        try:
            data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
            configs = data.get("configs", [])
        except Exception as exc:
            log.error("seed.parse_error", error=str(exc))
            return

        created = 0
        for raw in configs:
            try:
                payload = ConfigCreate.model_validate(raw)
                await config_service.create_config(session, payload)
                created += 1
            except Exception as exc:
                log.warning("seed.config_error", name=raw.get("name"), error=str(exc))

        log.info("seed.done", created=created)
