from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import execute_run
from app.api.deps import db_session
from app.models.run import RunTrigger
from app.schemas.event import EventOut
from app.schemas.run import RunOut
from app.services import config_service, run_service

router = APIRouter(tags=["runs"])


def _config_snapshot(obj) -> dict:
    return {
        "id": str(obj.id),
        "name": obj.name,
        "topic": obj.topic,
        "focus_areas": obj.focus_areas or [],
        "schedule_cron": obj.schedule_cron,
        "timezone": obj.timezone,
        "recipients": obj.recipients or [],
        "search_config": obj.search_config or {},
        "llm_config": obj.llm_config or {},
        "dedup_window_days": obj.dedup_window_days,
        "pdf_template": obj.pdf_template,
        "max_pages": obj.max_pages,
    }


@router.post(
    "/configs/{config_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_run(
    config_id: UUID, session: AsyncSession = Depends(db_session)
) -> RunOut:
    cfg = await config_service.get_config(session, config_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="config not found")
    run = await run_service.create_run(session, config_id, RunTrigger.MANUAL)
    asyncio.create_task(execute_run(str(run.id), _config_snapshot(cfg)))
    return RunOut.model_validate(run)


@router.get("/runs", response_model=list[RunOut])
async def list_runs(
    config_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(db_session),
) -> list[RunOut]:
    items = await run_service.list_runs(session, config_id=config_id, status=status_filter, limit=limit)
    return [RunOut.model_validate(i) for i in items]


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(run_id: UUID, session: AsyncSession = Depends(db_session)) -> RunOut:
    run = await run_service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return RunOut.model_validate(run)


@router.get("/runs/{run_id}/events", response_model=list[EventOut])
async def list_run_events(
    run_id: UUID,
    after_id: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
    session: AsyncSession = Depends(db_session),
) -> list[EventOut]:
    run = await run_service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    events = await run_service.list_events(session, run_id, after_id=after_id, limit=limit)
    return [
        EventOut(
            id=e.id,
            run_id=e.run_id,
            ts=e.ts,
            node=e.node,
            type=e.event_type,
            payload=e.payload,
        )
        for e in events
    ]


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_run(run_id: UUID, session: AsyncSession = Depends(db_session)) -> dict:
    ok = await run_service.cancel_run(session, run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="run not found or already terminal")
    return {"status": "cancelled"}
