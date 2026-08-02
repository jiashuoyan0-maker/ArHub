"""Persistent workflow state machine for ArHub skills."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

try:
    from config import BACKEND_DIR, SKILLS_DIR, WORKSPACES_DIR
    from models.schemas import StepStatus, WorkflowStatus
    from services.claude_runner import claude_runner
    from services.docx_exporter import export_markdown_to_docx
    from services.state_store import (
        append_log,
        create_checkpoint,
        create_workflow,
        get_db,
        get_pending_checkpoint,
        get_workflow,
        resolve_checkpoint_record,
        update_step,
        update_workflow,
    )
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import BACKEND_DIR, SKILLS_DIR, WORKSPACES_DIR
    from backend.models.schemas import StepStatus, WorkflowStatus
    from backend.services.claude_runner import claude_runner
    from backend.services.docx_exporter import export_markdown_to_docx
    from backend.services.state_store import (
        append_log,
        create_checkpoint,
        create_workflow,
        get_db,
        get_pending_checkpoint,
        get_workflow,
        resolve_checkpoint_record,
        update_step,
        update_workflow,
    )

log = logging.getLogger(__name__)

Broadcast = Callable[[str, dict[str, Any]], Awaitable[None] | None]


@dataclass(frozen=True)
class StepDef:
    skill_name: str
    display_name: str
    output_files: list[str] = field(default_factory=list)
    primary_output: str | None = None
    has_checkpoint: bool = False
    checkpoint_type: str | None = None


@dataclass(frozen=True)
class TemplateDef:
    pipeline_skill: str
    display_name: str
    sub_steps: list[StepDef]


def _load_templates() -> dict[str, TemplateDef]:
    source = BACKEND_DIR / "workflow_templates.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    return {
        name: TemplateDef(
            pipeline_skill=item["pipeline_skill"],
            display_name=item["display_name"],
            sub_steps=[StepDef(**step) for step in item["sub_steps"]],
        )
        for name, item in raw.items()
    }


TEMPLATES = _load_templates()


async def _noop_broadcast(workflow_id: str, event: dict[str, Any]) -> None:
    return None


_broadcast: Broadcast = _noop_broadcast


def set_broadcast(fn: Broadcast) -> None:
    global _broadcast
    _broadcast = fn


async def _emit(workflow_id: str, event: dict[str, Any]) -> None:
    payload = {"workflow_id": workflow_id, **event}
    result = _broadcast(workflow_id, payload)
    if inspect.isawaitable(result):
        await result


async def _log_event(
    workflow_id: str,
    message: str,
    *,
    step_name: str | None = None,
    level: str = "info",
) -> None:
    await append_log(workflow_id, message, step_name=step_name, level=level)
    await _emit(
        workflow_id,
        {"type": "step_progress", "step": step_name, "level": level, "log": message},
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _template_for(name: str) -> TemplateDef:
    try:
        return TEMPLATES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown workflow template: {name}") from exc


def _step_def(template_name: str, skill_name: str) -> StepDef:
    for step in _template_for(template_name).sub_steps:
        if step.skill_name == skill_name:
            return step
    raise ValueError(f"Skill {skill_name!r} is not part of template {template_name!r}")


def _workspace_file_list(workspace: Path) -> list[str]:
    result: list[str] = []
    for path in workspace.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            result.append(path.relative_to(workspace).as_posix())
        if len(result) >= 3000:
            break
    return sorted(result)


def _existing_expected_files(workspace: Path, step: StepDef) -> list[str]:
    result = []
    for name in step.output_files:
        if (workspace / name).exists():
            result.append(name)
    return result


def _docx_source_file(workspace: Path, step: StepDef) -> str | None:
    candidates = [step.primary_output, *step.output_files]
    for output_name in candidates:
        if not output_name or Path(output_name).suffix.lower() != ".docx":
            continue
        source = Path(output_name).with_suffix(".md")
        if (workspace / source).is_file():
            return source.as_posix()
    return None


async def _run_docx_export_step(
    workflow: dict[str, Any], step: StepDef, workspace: Path
) -> dict[str, Any]:
    source_file = _docx_source_file(workspace, step)
    exported = await export_markdown_to_docx(
        workspace,
        source_file=source_file,
        template=workflow["template"],
    )
    if not exported.get("success", True):
        raise RuntimeError(str(exported.get("error") or "DOCX export failed"))

    output_path = Path(exported["output_path"]).resolve()
    try:
        output_file = output_path.relative_to(workspace).as_posix()
    except ValueError as exc:
        raise RuntimeError("DOCX exporter returned a file outside the workspace") from exc

    source_path = Path(exported.get("source_path") or source_file or "")
    engine = str(exported.get("engine") or "unknown")
    output = f"Exported {source_path.name} to {output_file} with the {engine} engine."
    export_log = str(exported.get("log") or "").strip()
    if export_log:
        output += f"\n{export_log}"

    return {
        "success": True,
        "output": output,
        "output_files": [output_file],
        "engine": engine,
        "source_path": str(source_path),
        "output_path": str(output_path),
        "size": exported.get("size"),
        "log": export_log,
    }


def _primary_preview(workspace: Path, step: StepDef) -> tuple[str | None, str | None]:
    if not step.primary_output:
        return None, None
    path = (workspace / step.primary_output).resolve()
    try:
        path.relative_to(workspace)
    except ValueError:
        return None, None
    if not path.is_file() or path.stat().st_size > 300_000:
        return step.primary_output, None
    try:
        return step.primary_output, path.read_text(encoding="utf-8")[:100_000]
    except (OSError, UnicodeDecodeError):
        return step.primary_output, None


async def create_new_workflow(
    template: str,
    title: str,
    params: dict[str, Any],
    enable_checkpoints: bool = False,
) -> str:
    template_def = _template_for(template)
    workflow_id = uuid.uuid4().hex
    workspace = (Path(WORKSPACES_DIR) / workflow_id).resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    workflow = {
        "id": workflow_id,
        "template": template,
        "title": title.strip(),
        "params": params or {},
        "status": WorkflowStatus.PENDING.value,
        "workspace_dir": str(workspace),
        "enable_checkpoints": bool(enable_checkpoints),
        "steps": [
            {
                "skill_name": step.skill_name,
                "display_name": step.display_name,
                "step_order": order,
                "status": StepStatus.PENDING.value,
                "has_checkpoint": step.has_checkpoint,
                "checkpoint_type": step.checkpoint_type,
                "output_files": [],
                "primary_output": step.primary_output,
            }
            for order, step in enumerate(template_def.sub_steps)
        ],
    }
    db = await get_db()
    try:
        await create_workflow(db, workflow)
    except Exception:
        workspace.rmdir()
        raise
    finally:
        await db.close()
    await _log_event(workflow_id, f"Created workflow: {title}")
    return workflow_id


def load_prompt(name: str, **variables: Any) -> str:
    path = BACKEND_DIR / "services" / "prompts" / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


async def _read_workflow(workflow_id: str) -> dict[str, Any]:
    db = await get_db()
    try:
        workflow = await get_workflow(db, workflow_id)
    finally:
        await db.close()
    if workflow is None:
        raise KeyError(workflow_id)
    return workflow


async def run_single_step(workflow_id: str, skill_name: str) -> dict[str, Any]:
    workflow = await _read_workflow(workflow_id)
    step_row = next(
        (item for item in workflow["steps"] if item["skill_name"] == skill_name), None
    )
    if step_row is None:
        raise ValueError(f"Unknown workflow step: {skill_name}")
    step = _step_def(workflow["template"], skill_name)
    workspace = Path(workflow["workspace_dir"]).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    db = await get_db()
    try:
        await update_workflow(
            db, workflow_id, status=WorkflowStatus.RUNNING.value, current_step=skill_name
        )
        await update_step(
            db,
            workflow_id,
            skill_name,
            status=StepStatus.RUNNING.value,
            started_at=_now(),
            completed_at=None,
            error_message=None,
        )
    finally:
        await db.close()

    await _emit(
        workflow_id,
        {"type": "step_started", "step": skill_name, "display_name": step.display_name},
    )
    await _log_event(workflow_id, f"Starting {step.display_name}", step_name=skill_name)

    async def on_output(text: str) -> None:
        clean = text.strip()
        if clean:
            await _log_event(workflow_id, clean[-4000:], step_name=skill_name, level="progress")

    params = dict(workflow.get("params") or {})
    feedback_map = params.get("_checkpoint_feedback") or {}
    feedback = feedback_map.get(skill_name) if isinstance(feedback_map, dict) else None
    arguments = workflow["title"]
    if feedback:
        arguments += f"\n\nUser checkpoint feedback:\n{feedback}"
    if skill_name == "docx-export":
        try:
            result = await _run_docx_export_step(workflow, step, workspace)
        except Exception as exc:
            log.exception("DOCX export failed for workflow %s", workflow_id)
            result = {"success": False, "error": f"DOCX export failed: {exc}"}
    else:
        result = await claude_runner.run_skill(
            skill_name,
            arguments,
            workspace,
            f"{workflow_id}:{skill_name}",
            on_output=on_output,
            extra_params=params,
            workspace_files=_workspace_file_list(workspace),
            context_summary=str(feedback or ""),
        )

    latest = await _read_workflow(workflow_id)
    if result.get("cancelled") or (
        not result.get("success") and latest["status"] == WorkflowStatus.PAUSED.value
    ):
        db = await get_db()
        try:
            await update_step(
                db,
                workflow_id,
                skill_name,
                status=StepStatus.PENDING.value,
                error_message=None,
            )
        finally:
            await db.close()
        return {**result, "paused": True}

    if not result.get("success"):
        error = str(result.get("error") or "Agent step failed")
        db = await get_db()
        try:
            await update_step(
                db,
                workflow_id,
                skill_name,
                status=StepStatus.FAILED.value,
                completed_at=_now(),
                error_message=error,
            )
            await update_workflow(db, workflow_id, status=WorkflowStatus.FAILED.value)
        finally:
            await db.close()
        await _log_event(workflow_id, error, step_name=skill_name, level="error")
        await _emit(
            workflow_id, {"type": "step_failed", "step": skill_name, "error": error}
        )
        raise RuntimeError(error)

    output_files = sorted(
        set(result.get("output_files") or [])
        | set(_existing_expected_files(workspace, step))
    )
    missing_files = [name for name in step.output_files if not (workspace / name).exists()]
    db = await get_db()
    try:
        await update_step(
            db,
            workflow_id,
            skill_name,
            status=StepStatus.COMPLETED.value,
            output_files=output_files,
            completed_at=_now(),
            error_message=None,
        )
    finally:
        await db.close()
    await _log_event(workflow_id, f"Completed {step.display_name}", step_name=skill_name)
    await _emit(
        workflow_id,
        {
            "type": "step_completed",
            "step": skill_name,
            "output_files": output_files,
            "missing_files": missing_files,
            "result_summary": str(result.get("output") or "")[-1000:],
        },
    )
    return {**result, "output_files": output_files, "missing_files": missing_files}


async def _hit_checkpoint(
    workflow: dict[str, Any], step_row: dict[str, Any], step: StepDef
) -> None:
    workflow_id = workflow["id"]
    workspace = Path(workflow["workspace_dir"]).resolve()
    primary_file, primary_content = _primary_preview(workspace, step)
    data = {
        "display_name": step.display_name,
        "primary_output_file": primary_file,
        "primary_output_content": primary_content,
    }
    db = await get_db()
    try:
        await create_checkpoint(
            db,
            workflow_id,
            step.skill_name,
            step.checkpoint_type or "approve",
            data,
        )
        await update_step(
            db,
            workflow_id,
            step.skill_name,
            status=StepStatus.WAITING_CHECKPOINT.value,
        )
        await update_workflow(db, workflow_id, status=WorkflowStatus.PAUSED.value)
    finally:
        await db.close()
    await _emit(
        workflow_id,
        {
            "type": "checkpoint_hit",
            "step": step.skill_name,
            "display_name": step.display_name,
            "checkpoint_type": step.checkpoint_type or "approve",
            **data,
        },
    )


async def run_workflow(workflow_id: str) -> None:
    try:
        workflow = await _read_workflow(workflow_id)
        db = await get_db()
        try:
            pending_checkpoint = await get_pending_checkpoint(db, workflow_id)
            if pending_checkpoint:
                return
            await update_workflow(db, workflow_id, status=WorkflowStatus.RUNNING.value)
        finally:
            await db.close()
        await _emit(workflow_id, {"type": "workflow_started"})

        for initial_step in workflow["steps"]:
            current = await _read_workflow(workflow_id)
            if current["status"] == WorkflowStatus.PAUSED.value:
                await _emit(workflow_id, {"type": "workflow_paused"})
                return
            step_row = next(
                item
                for item in current["steps"]
                if item["skill_name"] == initial_step["skill_name"]
            )
            if step_row["status"] in {
                StepStatus.COMPLETED.value,
                StepStatus.SKIPPED.value,
            }:
                await _emit(
                    workflow_id,
                    {"type": "step_skipped", "step": step_row["skill_name"]},
                )
                continue
            if step_row["status"] == StepStatus.WAITING_CHECKPOINT.value:
                return

            result = await run_single_step(workflow_id, step_row["skill_name"])
            if result.get("paused"):
                await _emit(workflow_id, {"type": "workflow_paused"})
                return
            current = await _read_workflow(workflow_id)
            step = _step_def(current["template"], step_row["skill_name"])
            if current["enable_checkpoints"] and step.has_checkpoint:
                await _hit_checkpoint(current, step_row, step)
                return

        db = await get_db()
        try:
            await update_workflow(
                db,
                workflow_id,
                status=WorkflowStatus.COMPLETED.value,
                current_step=None,
            )
        finally:
            await db.close()
        await _log_event(workflow_id, "Workflow completed")
        await _emit(workflow_id, {"type": "workflow_completed"})
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        log.exception("Workflow %s failed", workflow_id)
        try:
            db = await get_db()
            try:
                await update_workflow(
                    db, workflow_id, status=WorkflowStatus.FAILED.value
                )
            finally:
                await db.close()
            await _log_event(workflow_id, str(exc), level="error")
            await _emit(
                workflow_id, {"type": "workflow_failed", "error": str(exc)}
            )
        except Exception:
            log.exception("Could not persist workflow failure")


async def resolve_checkpoint(workflow_id: str, response: dict[str, Any]) -> dict[str, Any]:
    action = str(response.get("action") or "").lower()
    if action not in {"approve", "feedback", "stop"}:
        raise ValueError(f"Unsupported checkpoint action: {action}")
    db = await get_db()
    try:
        checkpoint = await get_pending_checkpoint(db, workflow_id)
        if checkpoint is None:
            raise LookupError("No pending checkpoint")
        await resolve_checkpoint_record(db, checkpoint["id"], response)
        workflow = await get_workflow(db, workflow_id)
        if workflow is None:
            raise KeyError(workflow_id)
        step_name = checkpoint["step_name"]
        if action == "stop":
            await update_step(
                db,
                workflow_id,
                step_name,
                status=StepStatus.COMPLETED.value,
            )
            await update_workflow(
                db, workflow_id, status=WorkflowStatus.PAUSED.value, current_step=None
            )
        elif action == "feedback":
            params = dict(workflow.get("params") or {})
            feedback_map = dict(params.get("_checkpoint_feedback") or {})
            feedback_map[step_name] = str((response.get("data") or {}).get("feedback") or "")
            params["_checkpoint_feedback"] = feedback_map
            await update_step(
                db,
                workflow_id,
                step_name,
                status=StepStatus.PENDING.value,
                completed_at=None,
                error_message=None,
            )
            await update_workflow(
                db,
                workflow_id,
                status=WorkflowStatus.PENDING.value,
                params=params,
            )
        else:
            await update_step(
                db,
                workflow_id,
                step_name,
                status=StepStatus.COMPLETED.value,
            )
            await update_workflow(
                db, workflow_id, status=WorkflowStatus.PENDING.value
            )
    finally:
        await db.close()
    if action == "stop":
        await _emit(workflow_id, {"type": "workflow_stopped"})
        return {"status": "stopped", "resume": False}
    return {"status": "accepted", "action": action, "resume": True}


async def wait_checkpoint(workflow_id: str, timeout: int = 600) -> dict[str, Any]:
    """Compatibility helper for callers that still poll checkpoint resolution."""
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        db = await get_db()
        try:
            checkpoint = await get_pending_checkpoint(db, workflow_id)
        finally:
            await db.close()
        if checkpoint is None:
            return {"action": "approve", "data": {}}
        await asyncio.sleep(0.5)
    return {"action": "approve", "data": {"feedback": "(automatic approval)"}}
