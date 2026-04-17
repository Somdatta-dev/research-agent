from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(monkeypatch):
    # Minimal env so Settings() can load during app import.
    for k, v in {
        "DATABASE_URL": "postgresql+asyncpg://x:x@localhost/x",
        "LG_CHECKPOINT_DB_URL": "postgresql://x:x@localhost/x",
        "REDIS_URL": "redis://localhost:6379/0",
        "LLM_BASE_URL": "https://x",
        "LLM_API_KEY": "x",
        "LLM_MODEL_PRIMARY": "x",
        "LLM_MODEL_FAST": "x",
        "TAVILY_API_KEY": "x",
        "BRAVE_API_KEY": "x",
        "SMTP_HOST": "x",
        "SMTP_USERNAME": "x",
        "SMTP_PASSWORD": "x",
        "EMAIL_FROM_NAME": "x",
        "EMAIL_FROM_ADDRESS": "x@x",
    }.items():
        monkeypatch.setenv(k, v)

    from app.main import create_app

    client = TestClient(create_app())
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
