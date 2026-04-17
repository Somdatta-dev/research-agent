from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.llm_config import LLMConfig, LLMTierOverride

Tier = Literal["primary", "fast"]

DEFAULT_MAX_TOKENS = 8192


class ReasoningChatOpenAI(ChatOpenAI):
    """ChatOpenAI subclass that preserves reasoning_content from
    OpenAI-compatible reasoning models (GPT-5, Magistral, DeepSeek-R1, etc.).

    langchain-openai silently drops the reasoning_content field
    (see langchain-ai/langchain#35059). This override:
    1. Stashes reasoning_content in additional_kwargs
    2. Falls back to reasoning_content when content is null
    """

    def _create_chat_result(self, response, generation_info=None):
        chat_result = super()._create_chat_result(response, generation_info)

        response_dict = (
            response if isinstance(response, dict) else response.model_dump()
        )
        choices = response_dict.get("choices", [])
        for i, gen in enumerate(chat_result.generations):
            if i >= len(choices):
                break
            msg_dict = choices[i].get("message", {})
            reasoning = msg_dict.get("reasoning_content") or msg_dict.get("reasoning")
            if reasoning and isinstance(gen.message, AIMessage):
                gen.message.additional_kwargs["reasoning_content"] = reasoning
                if not gen.message.content:
                    gen.message.content = reasoning

        return chat_result


def _env_defaults(tier: Tier) -> LLMTierOverride:
    if tier == "primary":
        return LLMTierOverride(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model_primary,
            temperature=0.3,
            timeout_s=settings.llm_timeout_s,
        )
    return LLMTierOverride(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model_fast,
        temperature=0.2,
        timeout_s=settings.llm_timeout_s,
    )


def resolve_llm(
    tier: Tier,
    config: LLMConfig | None = None,
    *,
    tags: list[str] | None = None,
) -> ReasoningChatOpenAI:
    """Single source of truth for building an LLM client.
    Layer 1 (config) overrides Layer 2 (env). No hardcoded fallbacks."""
    env = _env_defaults(tier)
    override = (
        (config.primary if tier == "primary" else config.fast)
        if config
        else LLMTierOverride()
    )

    timeout_s = override.timeout_s or env.timeout_s
    reasoning_effort = settings.llm_reasoning_effort

    kwargs: dict[str, Any] = {
        "base_url": override.base_url or env.base_url,
        "api_key": override.api_key or env.api_key,
        "model": override.model or env.model,
        "max_tokens": override.max_tokens or DEFAULT_MAX_TOKENS,
        "timeout": timeout_s,
        "max_retries": settings.llm_max_retries,
    }

    if reasoning_effort:
        # Reasoning models (GPT-5, o-series) reject temperature/top_p.
        kwargs["reasoning_effort"] = reasoning_effort
    else:
        kwargs["temperature"] = (
            override.temperature if override.temperature is not None else env.temperature
        )

    return ReasoningChatOpenAI(**kwargs).with_config(tags=tags or [])
