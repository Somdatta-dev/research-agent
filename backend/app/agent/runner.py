from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import build_graph
from app.agent.state import ReportState
from app.core.config import settings
from app.core.events import publish_event
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.run import Run, RunStatus
from app.models.run_event import RunEvent

log = get_logger(__name__)

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None
_compiled_graph = None


async def setup_checkpointer() -> None:
    global _pool, _checkpointer, _compiled_graph
    _pool = AsyncConnectionPool(
        conninfo=settings.lg_checkpoint_db_url,
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )
    await _pool.open()
    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()

    graph = build_graph()
    _compiled_graph = graph.compile(checkpointer=_checkpointer)
    log.info("checkpointer.ready")


async def teardown_checkpointer() -> None:
    global _pool, _checkpointer, _compiled_graph
    if _pool:
        await _pool.close()
    _pool = None
    _checkpointer = None
    _compiled_graph = None


async def _persist_event(
    session: AsyncSession, run_id: str, node: str | None, event_type: str, payload: dict
) -> None:
    ts = datetime.now(timezone.utc)
    event = RunEvent(
        run_id=run_id,
        ts=ts,
        node=node,
        event_type=event_type,
        payload=payload,
    )
    session.add(event)
    await session.commit()
    try:
        await publish_event(run_id, {
            "run_id": run_id, "ts": ts.isoformat(), "node": node,
            "type": event_type, "payload": payload,
        })
    except Exception:
        pass


async def _update_run(
    session: AsyncSession,
    run_id: str,
    *,
    status: str | None = None,
    current_node: str | None = None,
    pdf_path: str | None = None,
    email_result: dict | None = None,
    error: str | None = None,
    metrics: dict | None = None,
) -> None:
    run = await session.get(Run, run_id)
    if not run:
        return
    if status:
        run.status = status
    if current_node is not None:
        run.current_node = current_node
    if status == RunStatus.RUNNING.value and not run.started_at:
        run.started_at = datetime.now(timezone.utc)
    if status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value):
        run.completed_at = datetime.now(timezone.utc)
    if pdf_path:
        run.pdf_path = pdf_path
    if email_result is not None:
        run.email_status = email_result
    if error:
        run.error = error
    if metrics:
        run.metrics = metrics
    await session.commit()


async def execute_run(run_id: str, config_snapshot: dict) -> None:
    if _compiled_graph is None:
        log.error("runner.no_graph", run_id=run_id)
        return

    initial_state: ReportState = {
        "run_id": run_id,
        "config": config_snapshot,
        "plan": [],
        "raw_hits": [],
        "deduped_hits": [],
        "enriched_hits": [],
        "sections": [],
        "cover_blurb": "",
        "draft_markdown": "",
        "pdf_path": None,
        "email_result": None,
        "errors": [],
    }

    run_config = {
        "configurable": {"thread_id": run_id},
        "max_concurrency": settings.agent_max_concurrency,
    }

    async with AsyncSessionLocal() as session:
        await _update_run(session, run_id, status=RunStatus.RUNNING.value)
        await _persist_event(session, run_id, None, "run_started", {})

    try:
        async for chunk in _compiled_graph.astream(
            initial_state,
            config=run_config,
            stream_mode=["updates", "custom", "messages"],
        ):
            mode, payload = chunk
            async with AsyncSessionLocal() as session:
                if mode == "updates":
                    for node_name, update in (payload or {}).items():
                        await _persist_event(
                            session, run_id, node_name, "node_completed", {}
                        )
                        await _update_run(
                            session,
                            run_id,
                            current_node=node_name,
                            pdf_path=update.get("pdf_path"),
                            email_result=update.get("email_result"),
                        )
                elif mode == "custom":
                    event_type = payload.get("type", "custom") if isinstance(payload, dict) else "custom"
                    await _persist_event(
                        session, run_id, None, event_type, payload if isinstance(payload, dict) else {}
                    )
                elif mode == "messages":
                    pass

        async with AsyncSessionLocal() as session:
            await _update_run(session, run_id, status=RunStatus.COMPLETED.value)
            await _persist_event(session, run_id, None, "run_completed", {})

    except Exception as exc:
        log.error("runner.failed", run_id=run_id, error=str(exc))
        async with AsyncSessionLocal() as session:
            await _update_run(
                session, run_id, status=RunStatus.FAILED.value, error=str(exc)
            )
            await _persist_event(
                session, run_id, None, "run_failed", {"error": str(exc)}
            )
