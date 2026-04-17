from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import subscribe_run
from app.db.session import AsyncSessionLocal
from app.services.run_service import list_events

router = APIRouter()


@router.websocket("/ws/runs/{run_id}")
async def ws_run_events(websocket: WebSocket, run_id: UUID) -> None:
    await websocket.accept()

    async with AsyncSessionLocal() as session:
        events = await list_events(session, run_id)
        for e in events:
            await websocket.send_json({
                "id": e.id,
                "run_id": str(e.run_id),
                "ts": e.ts.isoformat() if e.ts else None,
                "node": e.node,
                "type": e.event_type,
                "payload": e.payload or {},
            })

    ps = await subscribe_run(str(run_id))
    try:
        async for msg in ps.listen():
            if msg.get("type") == "message":
                data = msg.get("data", "")
                await websocket.send_text(data if isinstance(data, str) else json.dumps(data))
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        await ps.unsubscribe(f"run:{run_id}")
