from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "production"
    log_level: str = "INFO"
    timezone: str = "UTC"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str
    lg_checkpoint_db_url: str
    lg_checkpoint_schema: str = "langgraph"
    redis_url: str

    llm_base_url: str
    llm_api_key: str
    llm_model_primary: str
    llm_model_fast: str
    llm_timeout_s: int = 60
    llm_max_retries: int = 3
    llm_reasoning_effort: str | None = None  # "minimal" | "low" | "medium" | "high"

    run_token_budget: int = 200_000
    run_usd_budget: float = 2.50

    tavily_api_key: str
    brave_api_key: str
    search_default_recency_days: int = 2
    search_max_results_per_query: int = 10

    agent_max_concurrency: int = 4
    enrich_max_parallel: int = 4

    smtp_host: str
    smtp_port: int = 465
    smtp_use_ssl: bool = True
    smtp_username: str
    smtp_password: str
    email_from_name: str
    email_from_address: str

    reports_dir: str = "/data/reports"

    cors_allow_origins: str = "*"


settings = Settings()
