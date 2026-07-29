"""Persistent checkpoint query and resolution API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

try:
    from models.schemas import CheckpointResponse
    from services.state_store import get_db, get_pending_checkpoint, get_workflow
    from services.workflow_engine import resolve_checkpoint
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.models.schemas import CheckpointResponse
    from backend.services.state_store import get_db, get_pending_checkpoint, get_workflow
    from backend.services.workflow_engine import resolve_checkpoint

router = APIRouter(prefix="/api/workflows/{wf_id}/checkpoints", tags=["checkpoints"])


@router.get("/current")
async def get_current_checkpoint(wf_id: str) -> dict[str, Any]:
    db = await get_db()
    try:
        if await get_workflow(db, wf_id) is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        checkpoint = await get_pending_checkpoint(db, wf_id)
    finally:
        await db.close()
    if checkpoint is None:
        raise HTTPException(status_code=404, detail="No pending checkpoint")
    return checkpoint


@router.post("/resolve")
async def resolve(wf_id: str, body: CheckpointResponse) -> dict[str, Any]:
    try:
        result = await resolve_checkpoint(wf_id, body.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workflow not found") from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail="No pending checkpoint") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.get("resume"):
        from routers.workflows import _schedule

        _schedule(wf_id)
    return result
