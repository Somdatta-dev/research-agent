from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus, RunTrigger
from app.models.run_event import RunEvent


async def create_run(
    session: AsyncSession, config_id: UUID, trigger: RunTrigger = RunTrigger.MANUAL
) -> Run:
    run = Run(config_id=config_id, status=RunStatus.PENDING.value, trigger=trigger.value)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_run(session: AsyncSession, run_id: UUID) -> Run | None:
    return await session.get(Run, run_id)


async def list_runs(
    session: AsyncSession,
    config_id: UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Run]:
    stmt = select(Run)
    if config_id is not None:
        stmt = stmt.where(Run.config_id == config_id)
    if status is not None:
        stmt = stmt.where(Run.status == status)
    stmt = stmt.order_by(Run.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_events(
    session: AsyncSession, run_id: UUID, after_id: int = 0, limit: int = 1000
) -> list[RunEvent]:
    stmt = (
        select(RunEvent)
        .where(RunEvent.run_id == run_id, RunEvent.id > after_id)
        .order_by(RunEvent.id.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def cancel_run(session: AsyncSession, run_id: UUID) -> bool:
    run = await session.get(Run, run_id)
    if run is None:
        return False
    if run.status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value):
        return False
    run.status = RunStatus.CANCELLED.value
    await session.commit()
    return True
