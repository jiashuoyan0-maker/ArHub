"""Sandboxed provider-neutral Agent runtime for the workspace editor."""

from __future__ import annotations

import asyncio
import filecmp
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from config import APPDATA_DIR
    from models.schemas import AgentEvent, AgentEventType
    from services.claude_runner import ClaudeRunner, claude_runner
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import APPDATA_DIR
    from backend.models.schemas import AgentEvent, AgentEventType
    from backend.services.claude_runner import ClaudeRunner, claude_runner


MAX_DIFF_TEXT = 2_000_000
MAX_LOG_LINES = 4000
_SKIP_PARTS = {".git", "__pycache__", ".pytest_cache"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return default


def _safe_target(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Agent path leaves the workflow workspace") from exc
    return target


def _workspace_files(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    if not root.is_dir():
        return result
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or path.is_symlink()
            or any(part in _SKIP_PARTS for part in path.relative_to(root).parts)
        ):
            continue
        result[path.relative_to(root).as_posix()] = path
    return result


def _binary(path: Path) -> bool:
    if path.stat().st_size > MAX_DIFF_TEXT:
        return True
    sample = path.read_bytes()[:8192]
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def build_diffs(original: Path, sandbox: Path) -> list[dict[str, Any]]:
    """Return deterministic text/binary changes between two workspace trees."""

    if not sandbox.is_dir():
        return []
    before_files = _workspace_files(original)
    after_files = _workspace_files(sandbox)
    result: list[dict[str, Any]] = []
    for relative in sorted(set(before_files) | set(after_files)):
        before = before_files.get(relative)
        after = after_files.get(relative)
        if before and after and filecmp.cmp(before, after, shallow=False):
            continue
        action = "created" if before is None else "deleted" if after is None else "modified"
        binary = _binary(after or before)  # type: ignore[arg-type]
        result.append(
            {
                "path": relative,
                "action": action,
                "binary": binary,
                "before": ""
                if binary or before is None
                else before.read_text(encoding="utf-8", errors="replace"),
                "after": ""
                if binary or after is None
                else after.read_text(encoding="utf-8", errors="replace"),
            }
        )
    return result


def _copy_workspace(source: Path, destination: Path) -> None:
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir(parents=True, exist_ok=True)
    for relative, path in _workspace_files(source).items():
        target = _safe_target(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


@dataclass
class AgentRun:
    workflow_id: str
    runner_id: str
    workspace: Path
    sandbox: Path
    logs: list[str] = field(default_factory=list)
    stream_text: str = ""
    diffs: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    running: bool = True
    sequence: int = 0
    queue: asyncio.Queue[dict[str, Any] | None] = field(default_factory=asyncio.Queue)
    task: asyncio.Task[None] | None = None


class EditorAgentManager:
    """Run editor-agent in a copy, then atomically apply changes with undo."""

    def __init__(
        self,
        runner: ClaudeRunner = claude_runner,
        state_root: str | Path | None = None,
    ) -> None:
        self.runner = runner
        self.state_root = Path(state_root or (Path(APPDATA_DIR) / "editor_state"))
        self._runs: dict[str, AgentRun] = {}

    def _key(self, workflow_id: str) -> str:
        return hashlib.sha256(workflow_id.encode("utf-8")).hexdigest()[:32]

    def _dir(self, workflow_id: str) -> Path:
        return self.state_root / self._key(workflow_id)

    def _sandbox(self, workflow_id: str) -> Path:
        return self._dir(workflow_id) / "sandbox"

    def _backup(self, workflow_id: str) -> Path:
        return self._dir(workflow_id) / "backup"

    def _result_path(self, workflow_id: str) -> Path:
        return self._dir(workflow_id) / "result.json"

    def _history_path(self, workflow_id: str) -> Path:
        return self._dir(workflow_id) / "history.json"

    def get_history(self, workflow_id: str) -> list[dict[str, Any]]:
        value = _read_json(self._history_path(workflow_id), [])
        return value if isinstance(value, list) else []

    def append_history(self, workflow_id: str, role: str, content: str) -> None:
        history = self.get_history(workflow_id)
        history.append({"role": role, "content": content, "created_at": _utc_now()})
        _atomic_json(self._history_path(workflow_id), history[-200:])

    def clear_history(self, workflow_id: str) -> None:
        path = self._history_path(workflow_id)
        path.unlink(missing_ok=True)

    def _backup_manifest(self, workflow_id: str) -> dict[str, Any]:
        value = _read_json(self._backup(workflow_id) / "manifest.json", {})
        return value if isinstance(value, dict) else {}

    def _save_result(self, workflow_id: str, result: dict[str, Any]) -> None:
        _atomic_json(self._result_path(workflow_id), result)

    @staticmethod
    async def _emit_event(
        run: AgentRun, event_type: AgentEventType, **data: Any
    ) -> None:
        legacy_types = {
            AgentEventType.STARTED: "progress",
            AgentEventType.TEXT_DELTA: "progress",
            AgentEventType.ACTIVITY: "log",
            AgentEventType.TOOL: "log",
            AgentEventType.COMPLETED: "result",
            AgentEventType.STOPPED: "result",
            AgentEventType.ERROR: "error",
        }
        run.sequence += 1
        event = AgentEvent(
            event=event_type,
            type=legacy_types[event_type],
            run_id=run.runner_id,
            sequence=run.sequence,
            timestamp=_utc_now(),
            data=data,
        )
        payload = event.model_dump(mode="json")
        # Transitional aliases keep the recovered React bundle operational while
        # new clients consume the versioned event/data envelope.
        if event_type == AgentEventType.TEXT_DELTA:
            payload.update(message=data.get("text", ""), streaming=True)
        elif event_type in {
            AgentEventType.STARTED,
            AgentEventType.ACTIVITY,
            AgentEventType.TOOL,
        }:
            payload["message"] = data.get("message", "")
        elif event_type in {
            AgentEventType.COMPLETED,
            AgentEventType.STOPPED,
            AgentEventType.ERROR,
        }:
            payload.update(data)
        await run.queue.put(payload)

    def _apply(
        self,
        workflow_id: str,
        workspace: Path,
        sandbox: Path,
        diffs: list[dict[str, Any]],
        selected: set[str] | None = None,
    ) -> list[str]:
        chosen = [item for item in diffs if selected is None or item["path"] in selected]
        if not chosen:
            return []
        backup = self._backup(workflow_id)
        shutil.rmtree(backup, ignore_errors=True)
        data_dir = backup / "files"
        manifest: dict[str, Any] = {"created_at": _utc_now(), "files": {}}
        for item in chosen:
            relative = item["path"]
            target = _safe_target(workspace, relative)
            entry = {"existed": target.is_file(), "action": item["action"]}
            manifest["files"][relative] = entry
            if target.is_file():
                stored = _safe_target(data_dir, relative)
                stored.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, stored)
        _atomic_json(backup / "manifest.json", manifest)

        applied: list[str] = []
        for item in chosen:
            relative = item["path"]
            target = _safe_target(workspace, relative)
            source = _safe_target(sandbox, relative)
            if item["action"] == "deleted":
                target.unlink(missing_ok=True)
            else:
                if not source.is_file():
                    raise FileNotFoundError(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + ".arhub.tmp")
                shutil.copy2(source, temporary)
                temporary.replace(target)
            applied.append(relative)
        return applied

    async def start(
        self,
        workflow_id: str,
        workspace: Path,
        message: str,
        *,
        mode: str,
        current_file: str = "",
        compile_log: str = "",
    ) -> AgentRun:
        current = self._runs.get(workflow_id)
        if current and current.running:
            raise RuntimeError("Editor Agent is already running")
        pending = build_diffs(workspace, self._sandbox(workflow_id))
        if pending:
            raise RuntimeError("Editor Agent has pending changes; apply or discard them first")

        sandbox = self._sandbox(workflow_id)
        _copy_workspace(workspace, sandbox)
        runner_id = f"{workflow_id}:editor"
        run = AgentRun(workflow_id, runner_id, workspace, sandbox)
        self._runs[workflow_id] = run
        self.append_history(workflow_id, "user", message)
        self._save_result(
            workflow_id,
            {
                "running": True,
                "logs": [],
                "stream_text": "",
                "diffs": [],
                "started_at": _utc_now(),
            },
        )
        await self._emit_event(
            run,
            AgentEventType.STARTED,
            message="Agent 已启动",
            workflow_id=workflow_id,
        )
        run.task = asyncio.create_task(
            self._execute(run, message, mode, current_file, compile_log),
            name=f"editor-agent:{workflow_id}",
        )
        return run

    async def _execute(
        self,
        run: AgentRun,
        message: str,
        mode: str,
        current_file: str,
        compile_log: str,
    ) -> None:
        last_stream_emit = 0.0
        last_stream_snapshot = ""

        async def on_output(output: str) -> None:
            lines = [line for line in output.replace("\r", "").split("\n") if line]
            for line in lines:
                run.logs.append(line[-4000:])
                if len(run.logs) > MAX_LOG_LINES:
                    del run.logs[: len(run.logs) - MAX_LOG_LINES]
                event_type = (
                    AgentEventType.TOOL if line.lstrip().startswith("[tool]")
                    else AgentEventType.ACTIVITY
                )
                await self._emit_event(run, event_type, message=line[-4000:])

        async def on_delta(delta: str) -> None:
            nonlocal last_stream_emit, last_stream_snapshot
            if not delta:
                return
            run.stream_text += delta
            now = asyncio.get_running_loop().time()
            if now - last_stream_emit < 0.05:
                return
            last_stream_emit = now
            last_stream_snapshot = run.stream_text
            await self._emit_event(
                run,
                AgentEventType.TEXT_DELTA,
                delta=delta,
                text=run.stream_text,
            )

        context = (
            f"WORKFLOW MODE: {mode.upper()}\n"
            f"CURRENT FILE: {current_file or '(none)'}\n"
            f"USER REQUEST: {message}"
        )
        if compile_log:
            context += f"\n\nCOMPILE OR RUNTIME LOG:\n{compile_log[-20_000:]}"

        try:
            runner_result = await self.runner.run_skill(
                "editor-agent",
                context,
                run.sandbox,
                run.runner_id,
                on_output=on_output,
                on_delta=on_delta,
                workspace_files=sorted(_workspace_files(run.sandbox)),
            )
            if run.stream_text and last_stream_snapshot != run.stream_text:
                await self._emit_event(
                    run,
                    AgentEventType.TEXT_DELTA,
                    delta=run.stream_text[len(last_stream_snapshot) :],
                    text=run.stream_text,
                )
            run.diffs = build_diffs(run.workspace, run.sandbox)
            success = bool(runner_result.get("success"))
            summary = str(
                runner_result.get("result")
                or runner_result.get("output")
                or runner_result.get("error")
                or "Agent 执行完成"
            ).strip()
            auto_applied: list[str] = []
            pending_diffs = run.diffs
            if success and run.diffs:
                auto_applied = self._apply(
                    run.workflow_id, run.workspace, run.sandbox, run.diffs
                )
                pending_diffs = []
                shutil.rmtree(run.sandbox, ignore_errors=True)
            run.diffs = pending_diffs
            run.result = {
                "type": "result",
                "summary": summary,
                "auto_applied": auto_applied,
                "diffs": pending_diffs,
                "logs": list(run.logs),
                "stream_text": run.stream_text,
                "auto_compiled": any(path.lower().endswith(".pdf") for path in auto_applied),
                "success": success,
            }
            self.append_history(run.workflow_id, "ai", summary)
            await self._emit_event(
                run,
                AgentEventType.COMPLETED,
                **run.result,
            )
        except asyncio.CancelledError:
            run.diffs = build_diffs(run.workspace, run.sandbox)
            run.result = {
                "type": "result",
                "summary": "Agent 已停止。未应用的修改仍可检查或放弃。",
                "auto_applied": [],
                "diffs": run.diffs,
                "logs": list(run.logs),
                "stream_text": run.stream_text,
                "auto_compiled": False,
                "success": False,
                "cancelled": True,
            }
            self.append_history(run.workflow_id, "system", run.result["summary"])
            await self._emit_event(run, AgentEventType.STOPPED, **run.result)
        except Exception as exc:
            run.diffs = build_diffs(run.workspace, run.sandbox)
            message_text = f"Agent failed: {type(exc).__name__}: {exc}"
            run.result = {
                "type": "error",
                "message": message_text,
                "summary": message_text,
                "auto_applied": [],
                "diffs": run.diffs,
                "logs": list(run.logs),
                "stream_text": run.stream_text,
                "auto_compiled": False,
                "success": False,
            }
            self.append_history(run.workflow_id, "system", message_text)
            await self._emit_event(run, AgentEventType.ERROR, **run.result)
        finally:
            run.running = False
            persisted = {**run.result, "running": False, "finished_at": _utc_now()}
            self._save_result(run.workflow_id, persisted)
            await run.queue.put(None)

    def check(
        self, workflow_id: str, workspace: Path, log_offset: int = 0
    ) -> dict[str, Any]:
        run = self._runs.get(workflow_id)
        if run:
            logs = run.logs
            diffs = run.diffs if not run.running else []
            result = run.result
            running = run.running
            stream_text = run.stream_text
        else:
            result = _read_json(self._result_path(workflow_id), {})
            if not isinstance(result, dict):
                result = {}
            running = False
            logs = result.get("logs") if isinstance(result.get("logs"), list) else []
            stream_text = str(result.get("stream_text") or "")
            diffs = build_diffs(workspace, self._sandbox(workflow_id))
            if result.get("running"):
                result["running"] = False
                result["summary"] = "Backend restarted before the Agent completed."
                result["diffs"] = diffs
                self._save_result(workflow_id, result)

        offset = min(max(0, log_offset), len(logs))
        manifest = self._backup_manifest(workflow_id)
        files = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
        applied = sorted(files)
        return {
            "running": running,
            "logs": logs[offset:],
            "log_offset": len(logs),
            "stream_text": stream_text,
            "diffs": diffs,
            "can_undo": bool(files),
            "applied_files": applied,
            "summary": result.get("summary", ""),
            "auto_applied": result.get("auto_applied", []),
            "auto_compiled": bool(result.get("auto_compiled")),
        }

    def apply(
        self, workflow_id: str, workspace: Path, paths: list[str]
    ) -> dict[str, Any]:
        sandbox = self._sandbox(workflow_id)
        diffs = build_diffs(workspace, sandbox)
        available = {item["path"] for item in diffs}
        selected = set(paths)
        unknown = selected - available
        if unknown:
            raise ValueError(f"Unknown pending paths: {', '.join(sorted(unknown))}")
        applied = self._apply(workflow_id, workspace, sandbox, diffs, selected)
        remaining = [item for item in diffs if item["path"] not in selected]
        if not remaining:
            shutil.rmtree(sandbox, ignore_errors=True)
        result = {
            "running": False,
            "summary": f"Applied {len(applied)} Agent change(s).",
            "auto_applied": applied,
            "diffs": remaining,
            "logs": [],
            "auto_compiled": any(path.lower().endswith(".pdf") for path in applied),
        }
        run = self._runs.get(workflow_id)
        if run:
            run.diffs = remaining
            run.result = result
        self._save_result(workflow_id, result)
        return {"ok": True, "applied": applied, "remaining": remaining}

    def discard(self, workflow_id: str) -> dict[str, Any]:
        run = self._runs.get(workflow_id)
        if run and run.running:
            raise RuntimeError("Stop the Agent before discarding its changes")
        shutil.rmtree(self._sandbox(workflow_id), ignore_errors=True)
        result = _read_json(self._result_path(workflow_id), {})
        if isinstance(result, dict):
            result.update({"running": False, "diffs": [], "auto_applied": []})
            self._save_result(workflow_id, result)
        if run:
            run.diffs = []
            run.result = result if isinstance(result, dict) else {}
        return {"ok": True, "discarded": True}

    def undo(self, workflow_id: str, workspace: Path) -> dict[str, Any]:
        backup = self._backup(workflow_id)
        manifest = self._backup_manifest(workflow_id)
        files = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
        if not files:
            return {"ok": True, "restored": []}
        restored: list[str] = []
        for relative, entry in files.items():
            target = _safe_target(workspace, relative)
            if bool(entry.get("existed")):
                source = _safe_target(backup / "files", relative)
                if source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            else:
                target.unlink(missing_ok=True)
            restored.append(relative)
        shutil.rmtree(backup, ignore_errors=True)
        return {"ok": True, "restored": sorted(restored)}

    def stop(self, workflow_id: str) -> bool:
        run = self._runs.get(workflow_id)
        if not run or not run.running:
            return False
        self.runner.cancel(run.runner_id)
        if run.task and not run.task.done():
            run.task.cancel()
        return True


editor_agent_manager = EditorAgentManager()
