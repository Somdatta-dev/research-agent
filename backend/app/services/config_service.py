from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_config import ReportConfig
from app.schemas.config import ConfigCreate, ConfigUpdate


def _payload_to_columns(data: dict) -> dict:
    """Pydantic nested models must be serialised to JSON-compatible dicts
    before hitting JSONB columns — SQLAlchemy won't call .model_dump() for us."""
    from pydantic import BaseModel

    out: dict = {}
    for k, v in data.items():
        if isinstance(v, BaseModel):
            out[k] = v.model_dump(mode="json")
        elif isinstance(v, list):
            out[k] = [i.model_dump(mode="json") if isinstance(i, BaseModel) else i for i in v]
        else:
            out[k] = v
    return out


async def create_config(session: AsyncSession, payload: ConfigCreate) -> ReportConfig:
    obj = ReportConfig(**_payload_to_columns(payload.model_dump()))
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def list_configs(
    session: AsyncSession, active: bool | None = None
) -> list[ReportConfig]:
    stmt = select(ReportConfig)
    if active is not None:
        stmt = stmt.where(ReportConfig.active == active)
    stmt = stmt.order_by(ReportConfig.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_config(session: AsyncSession, config_id: UUID) -> ReportConfig | None:
    return await session.get(ReportConfig, config_id)


async def update_config(
    session: AsyncSession, config_id: UUID, payload: ConfigUpdate
) -> ReportConfig | None:
    obj = await session.get(ReportConfig, config_id)
    if obj is None:
        return None
    updates = _payload_to_columns(payload.model_dump(exclude_unset=True))
    for k, v in updates.items():
        setattr(obj, k, v)
    await session.commit()
    await session.refresh(obj)
    return obj


async def soft_delete_config(session: AsyncSession, config_id: UUID) -> bool:
    obj = await session.get(ReportConfig, config_id)
    if obj is None:
        return False
    obj.active = False
    await session.commit()
    return True
