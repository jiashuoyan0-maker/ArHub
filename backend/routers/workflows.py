"""Workflow lifecycle, history and portable export API."""

from __future__ import annotations

import asyncio
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

try:
    from config import WORKSPACES_DIR
    from models.schemas import WorkflowCreate
    from services.claude_runner import claude_runner
    from services.state_store import (
        delete_workflow,
        export_workflow_data,
        get_db,
        get_pending_checkpoint,
        get_workflow,
        import_workflow_data,
        list_logs,
        list_workflows,
        reset_workflow,
        update_step,
        update_workflow,
    )
    from services.workflow_engine import (
        create_new_workflow,
        resolve_checkpoint,
        run_workflow,
    )
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import WORKSPACES_DIR
    from backend.models.schemas import WorkflowCreate
    from backend.services.claude_runner import claude_runner
    from backend.services.state_store import (
        delete_workflow,
        export_workflow_data,
        get_db,
        get_pending_checkpoint,
        get_workflow,
        import_workflow_data,
        list_logs,
        list_workflows,
        reset_workflow,
        update_step,
        update_workflow,
    )
    from backend.services.workflow_engine import (
        create_new_workflow,
        resolve_checkpoint,
        run_workflow,
    )

router = APIRouter(tags=["workflows"])
_tasks: dict[str, asyncio.Task[None]] = {}
_heartbeat_task: asyncio.Task[None] | None = None


def _schedule(workflow_id: str) -> asyncio.Task[None]:
    current = _tasks.get(workflow_id)
    if current and not current.done():
        return current
    task = asyncio.create_task(run_workflow(workflow_id), name=f"workflow:{workflow_id}")
    _tasks[workflow_id] = task

    def cleanup(done: asyncio.Task[None]) -> None:
        if _tasks.get(workflow_id) is done:
            _tasks.pop(workflow_id, None)

    task.add_done_callback(cleanup)
    return task


async def _workflow_or_404(workflow_id: str) -> dict[str, Any]:
    db = await get_db()
    try:
        workflow = await get_workflow(db, workflow_id)
    finally:
        await db.close()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


async def _heartbeat() -> None:
    while True:
        await asyncio.sleep(60)
        db = await get_db()
        try:
            workflows = await list_workflows(db)
        finally:
            await db.close()
        for workflow in workflows:
            workflow_id = workflow["id"]
            if workflow["status"] == "running" and not (
                workflow_id in _tasks and not _tasks[workflow_id].done()
            ):
                _schedule(workflow_id)


def start_heartbeat() -> None:
    global _heartbeat_task
    if _heartbeat_task is None or _heartbeat_task.done():
        _heartbeat_task = asyncio.create_task(_heartbeat(), name="workflow-heartbeat")


@router.post("/api/workflows", status_code=status.HTTP_201_CREATED)
async def create(body: WorkflowCreate) -> dict[str, Any]:
    workflow_id = await create_new_workflow(
        body.template.value,
        body.title,
        body.params,
        body.enable_checkpoints,
    )
    return {"id": workflow_id}


@router.get("/api/workflows")
async def list_all() -> list[dict[str, Any]]:
    db = await get_db()
    try:
        return await list_workflows(db)
    finally:
        await db.close()


@router.get("/api/workflows/{wf_id}")
async def get_one(wf_id: str) -> dict[str, Any]:
    return await _workflow_or_404(wf_id)


@router.get("/api/workflows/{wf_id}/logs")
async def get_logs(wf_id: str, limit: int = 500) -> list[dict[str, Any]]:
    await _workflow_or_404(wf_id)
    db = await get_db()
    try:
        return await list_logs(db, wf_id, limit)
    finally:
        await db.close()


@router.post("/api/workflows/{wf_id}/start")
async def start(wf_id: str) -> dict[str, Any]:
    workflow = await _workflow_or_404(wf_id)
    if workflow["status"] == "completed":
        raise HTTPException(status_code=409, detail="Workflow is already completed")
    db = await get_db()
    try:
        if await get_pending_checkpoint(db, wf_id):
            raise HTTPException(status_code=409, detail="Workflow is waiting for input")
        await update_workflow(db, wf_id, status="pending")
    finally:
        await db.close()
    _schedule(wf_id)
    return {"status": "started", "id": wf_id}


@router.post("/api/workflows/{wf_id}/pause")
async def pause(wf_id: str) -> dict[str, Any]:
    workflow = await _workflow_or_404(wf_id)
    claude_runner.cancel(wf_id)
    db = await get_db()
    try:
        await update_workflow(db, wf_id, status="paused")
        if workflow.get("current_step"):
            await update_step(
                db,
                wf_id,
                workflow["current_step"],
                status="pending",
                error_message=None,
            )
    finally:
        await db.close()
    return {"status": "paused"}


@router.post("/api/workflows/{wf_id}/resume")
async def resume(wf_id: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    db = await get_db()
    try:
        if await get_pending_checkpoint(db, wf_id):
            raise HTTPException(status_code=409, detail="Workflow is waiting for input")
        await update_workflow(db, wf_id, status="pending")
    finally:
        await db.close()
    _schedule(wf_id)
    return {"status": "resumed"}


async def _resolve_and_resume(wf_id: str, body: dict[str, Any]) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    try:
        result = await resolve_checkpoint(wf_id, body)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail="No pending checkpoint") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.get("resume"):
        _schedule(wf_id)
    return result


@router.post("/api/workflows/{wf_id}/checkpoint")
async def submit_checkpoint(wf_id: str, body: dict[str, Any]) -> dict[str, Any]:
    return await _resolve_and_resume(wf_id, body)


@router.post("/api/workflows/{wf_id}/restart")
async def restart(wf_id: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    claude_runner.cancel(wf_id)
    task = _tasks.get(wf_id)
    if task and not task.done():
        task.cancel()
    db = await get_db()
    try:
        await reset_workflow(db, wf_id)
    finally:
        await db.close()
    _schedule(wf_id)
    return {"status": "restarted"}


@router.post("/api/workflows/{wf_id}/steps/{skill_name}/rerun")
async def rerun_step(wf_id: str, skill_name: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    claude_runner.cancel(wf_id)
    db = await get_db()
    try:
        try:
            await reset_workflow(db, wf_id, from_step=skill_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Workflow step not found") from exc
    finally:
        await db.close()
    _schedule(wf_id)
    return {"status": "rerunning", "step": skill_name}


@router.delete("/api/workflows/{wf_id}")
async def delete(wf_id: str) -> dict[str, Any]:
    workflow = await _workflow_or_404(wf_id)
    claude_runner.cancel(wf_id)
    task = _tasks.pop(wf_id, None)
    if task and not task.done():
        task.cancel()
    db = await get_db()
    try:
        await delete_workflow(db, wf_id)
    finally:
        await db.close()
    workspace = Path(workflow.get("workspace_dir") or "").resolve()
    root = Path(WORKSPACES_DIR).resolve()
    if workspace != root:
        try:
            workspace.relative_to(root)
            shutil.rmtree(workspace, ignore_errors=True)
        except ValueError:
            pass
    return {"status": "deleted"}


def _add_export_to_zip(
    archive: zipfile.ZipFile,
    prefix: str,
    manifest: dict[str, Any],
    workspace: Path,
) -> None:
    archive.writestr(
        f"{prefix}manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
    )
    if not workspace.is_dir():
        return
    for path in workspace.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            relative = path.relative_to(workspace).as_posix()
            archive.write(path, f"{prefix}workspace/{relative}")


async def _build_export(ids: list[str]) -> io.BytesIO:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for workflow_id in ids:
            manifest = await export_workflow_data(workflow_id)
            if manifest is None:
                raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
            workspace = Path(manifest["workflow"].get("workspace_dir") or "")
            prefix = "" if len(ids) == 1 else f"workflows/{workflow_id}/"
            _add_export_to_zip(archive, prefix, manifest, workspace)
    output.seek(0)
    return output


def _zip_response(data: io.BytesIO, filename: str) -> StreamingResponse:
    encoded = quote(filename)
    return StreamingResponse(
        data,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.get("/api/workflows/{wf_id}/export")
async def export_one(wf_id: str) -> StreamingResponse:
    workflow = await _workflow_or_404(wf_id)
    data = await _build_export([wf_id])
    title = "".join(char if char.isalnum() else "_" for char in workflow["title"])[:60]
    return _zip_response(data, f"ArHub_{title or wf_id}.zip")


@router.post("/api/workflows/export-batch")
async def export_batch(body: dict[str, Any]) -> StreamingResponse:
    ids = [str(item) for item in body.get("ids", []) if item]
    if not ids:
        raise HTTPException(status_code=400, detail="No workflows selected")
    return _zip_response(await _build_export(ids), "ArHub_export.zip")


def _safe_zip_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive path: {name}")
    return path


@router.post("/api/workflows/import")
async def import_workflows(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    if len(raw) > 2_000_000_000:
        raise HTTPException(status_code=413, detail="Archive is too large")
    imported: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = {_safe_zip_member(info.filename): info for info in archive.infolist()}
            manifests = [path for path in members if path.name == "manifest.json"]
            if not manifests:
                raise ValueError("Archive does not contain manifest.json")
            for manifest_path in manifests:
                data = json.loads(archive.read(members[manifest_path]).decode("utf-8"))
                new_id = uuid.uuid4().hex
                workspace = (Path(WORKSPACES_DIR) / new_id).resolve()
                workspace.mkdir(parents=True, exist_ok=False)
                source_prefix = manifest_path.parent / "workspace"
                for member_path, info in members.items():
                    try:
                        relative = member_path.relative_to(source_prefix)
                    except ValueError:
                        continue
                    if not relative.parts or info.is_dir():
                        continue
                    destination = (workspace / Path(*relative.parts)).resolve()
                    destination.relative_to(workspace)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target)
                await import_workflow_data(data, new_id, str(workspace))
                workflow = data.get("workflow") or {}
                imported.append({"id": new_id, "title": workflow.get("title", new_id)})
    except (zipfile.BadZipFile, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid ArHub export: {exc}") from exc
    return {"count": len(imported), "imported": imported}
