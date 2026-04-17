from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.schemas.config import ConfigCreate, ConfigOut, ConfigUpdate
from app.services import config_service

router = APIRouter(prefix="/configs", tags=["configs"])


@router.post("", response_model=ConfigOut, status_code=status.HTTP_201_CREATED)
async def create(payload: ConfigCreate, session: AsyncSession = Depends(db_session)) -> ConfigOut:
    obj = await config_service.create_config(session, payload)
    from app.scheduler.service import add_job_for_config
    add_job_for_config(obj)
    return ConfigOut.model_validate(obj)


@router.get("", response_model=list[ConfigOut])
async def list_(
    active: bool | None = Query(default=None),
    session: AsyncSession = Depends(db_session),
) -> list[ConfigOut]:
    items = await config_service.list_configs(session, active=active)
    return [ConfigOut.model_validate(i) for i in items]


@router.get("/{config_id}", response_model=ConfigOut)
async def get(config_id: UUID, session: AsyncSession = Depends(db_session)) -> ConfigOut:
    obj = await config_service.get_config(session, config_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="config not found")
    return ConfigOut.model_validate(obj)


@router.put("/{config_id}", response_model=ConfigOut)
async def update(
    config_id: UUID,
    payload: ConfigUpdate,
    session: AsyncSession = Depends(db_session),
) -> ConfigOut:
    obj = await config_service.update_config(session, config_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="config not found")
    from app.scheduler.service import add_job_for_config
    add_job_for_config(obj)
    return ConfigOut.model_validate(obj)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete(config_id: UUID, session: AsyncSession = Depends(db_session)) -> None:
    ok = await config_service.soft_delete_config(session, config_id)
    if not ok:
        raise HTTPException(status_code=404, detail="config not found")
    from app.scheduler.service import remove_job_for_config
    remove_job_for_config(str(config_id))


@router.post("/{config_id}/test", status_code=status.HTTP_202_ACCEPTED)
async def test_dry_run(config_id: UUID, session: AsyncSession = Depends(db_session)) -> dict:
    """Dry-run with max_results=2 and no email. Wired up in Phase 3."""
    obj = await config_service.get_config(session, config_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="config not found")
    return {"status": "accepted", "note": "dry-run not yet implemented (Phase 3)"}
