from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    config_id: UUID
    status: str
    trigger: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_node: str | None = None
    pdf_path: str | None = None
    email_status: dict | None = None
    metrics: dict | None = None
    error: str | None = None
    created_at: datetime


class RunCreate(BaseModel):
    pass
