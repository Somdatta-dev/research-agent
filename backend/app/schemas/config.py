from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.llm_config import LLMConfig


class Recipient(BaseModel):
    email: EmailStr
    name: str | None = None


class SearchConfig(BaseModel):
    providers: list[str] = Field(default_factory=lambda: ["tavily", "brave"])
    max_results_per_query: int = 10
    recency_days: int = 2


class ConfigBase(BaseModel):
    name: str
    topic: str
    focus_areas: list[str] = Field(default_factory=list)
    schedule_cron: str
    timezone: str = "UTC"
    recipients: list[Recipient] = Field(default_factory=list)
    search_config: SearchConfig = Field(default_factory=SearchConfig)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    dedup_window_days: int = 7
    pdf_template: str = "linkedin_carousel"
    max_pages: int = 8
    active: bool = True

    @field_validator("schedule_cron")
    @classmethod
    def _validate_cron(cls, v: str) -> str:
        try:
            from croniter import croniter

            if not croniter.is_valid(v):
                raise ValueError(f"invalid cron expression: {v!r}")
        except ImportError:
            pass
        return v


class ConfigCreate(ConfigBase):
    pass


class ConfigUpdate(BaseModel):
    name: str | None = None
    topic: str | None = None
    focus_areas: list[str] | None = None
    schedule_cron: str | None = None
    timezone: str | None = None
    recipients: list[Recipient] | None = None
    search_config: SearchConfig | None = None
    llm_config: LLMConfig | None = None
    dedup_window_days: int | None = None
    pdf_template: str | None = None
    max_pages: int | None = None
    active: bool | None = None


class ConfigOut(ConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
