from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.config import settings
from app.services import run_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _safe_path(run_id: UUID) -> Path:
    base = Path(settings.reports_dir).resolve()
    target = (base / f"{run_id}.pdf").resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="invalid path")
    return target


@router.get("/{run_id}.pdf")
async def download_pdf(run_id: UUID, session: AsyncSession = Depends(db_session)) -> FileResponse:
    run = await run_service.get_run(session, run_id)
    if run is None or not run.pdf_path:
        raise HTTPException(status_code=404, detail="report not available yet")
    path = _safe_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="pdf file missing on disk")
    return FileResponse(path, media_type="application/pdf", filename=f"{run_id}.pdf")


@router.get("/{run_id}/preview")
async def preview(run_id: UUID) -> dict:
    """First-page PNG thumbnail. Wired up in Phase 6."""
    raise HTTPException(status_code=501, detail="preview not yet implemented (Phase 6)")
