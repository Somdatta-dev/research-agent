from __future__ import annotations

from pydantic import BaseModel, Field


class LLMTierOverride(BaseModel):
    """Per-report overrides for an LLM tier. Any unset field falls back to env defaults."""

    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_s: int | None = None


class LLMConfig(BaseModel):
    """Stored as the `llm_config` JSON column on report_configs."""

    primary: LLMTierOverride = Field(default_factory=LLMTierOverride)
    fast: LLMTierOverride = Field(default_factory=LLMTierOverride)
