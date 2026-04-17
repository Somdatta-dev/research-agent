from __future__ import annotations

import json

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def publish_event(run_id: str, event: dict) -> None:
    r = await get_redis()
    await r.publish(f"run:{run_id}", json.dumps(event, default=str))


async def subscribe_run(run_id: str) -> aioredis.client.PubSub:
    r = await get_redis()
    ps = r.pubsub()
    await ps.subscribe(f"run:{run_id}")
    return ps


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
