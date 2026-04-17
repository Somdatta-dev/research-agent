from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class ReportConfig(Base):
    __tablename__ = "report_configs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    focus_areas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    schedule_cron: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, server_default="UTC")
    recipients: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    search_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    llm_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    dedup_window_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="7")
    pdf_template: Mapped[str] = mapped_column(Text, nullable=False, server_default="linkedin_carousel")
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, server_default="8")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
