from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Event(BaseModel):
    """Normalized event envelope — persisted and fan-outed over Redis/WS."""

    run_id: UUID
    ts: datetime
    node: str | None = None
    type: str
    payload: dict[str, Any] = {}


class EventOut(Event):
    model_config = ConfigDict(from_attributes=True)

    id: int
