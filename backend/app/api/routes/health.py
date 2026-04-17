from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    checks: dict = {"db": "unknown", "redis": "unknown"}

    try:
        from app.db.session import engine

        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    try:
        from app.core.events import get_redis

        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    ok = checks["db"] == "ok" and checks["redis"] == "ok"
    return {
        "status": "ok" if ok else "degraded",
        "env": settings.app_env,
        "version": "0.1.0",
        "checks": checks,
    }
