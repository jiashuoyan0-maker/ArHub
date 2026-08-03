"""Open model Agent runtime with the legacy ``ClaudeRunner`` API surface."""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Awaitable, Callable

try:
    from config import CLAUDE_BIN, SKILLS_DIR
    from services.llm_client import chat_completion, message_text
    from services.state_store import get_all_settings
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import CLAUDE_BIN, SKILLS_DIR
    from backend.services.llm_client import chat_completion, message_text
    from backend.services.state_store import get_all_settings

log = logging.getLogger(__name__)

OutputCallback = Callable[[str], Awaitable[None] | None]
MAX_TOOL_OUTPUT = 60_000
MAX_FILE_READ = 100_000


AGENT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 2000},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or replace a UTF-8 text file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": "Replace one exact text occurrence in a workspace file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                },
                "required": ["path", "old_text", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List workspace files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "default": "**/*"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search text files in the workspace for a literal string or regex.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "pattern": {"type": "string", "default": "**/*"},
                    "regex": {"type": "boolean", "default": False},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a PowerShell command in the workspace and return stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 1800},
                },
                "required": ["command"],
            },
        },
    },
]


class ClaudeRunner:
    """Provider-neutral skill runner retaining the installed API contract."""

    def __init__(self) -> None:
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._processes: dict[str, set[asyncio.subprocess.Process]] = {}

    async def _emit(self, callback: OutputCallback | None, text: str) -> None:
        if callback is None or not text:
            return
        result = callback(text)
        if inspect.isawaitable(result):
            await result

    def is_running(self, workflow_id: str) -> bool:
        return workflow_id in self._cancel_events

    def cancel(self, workflow_id_prefix: str) -> bool:
        matched = False
        for workflow_id, event in list(self._cancel_events.items()):
            if workflow_id.startswith(workflow_id_prefix):
                matched = True
                event.set()
                for process in list(self._processes.get(workflow_id, ())):
                    if process.returncode is None:
                        process.terminate()
        return matched

    @staticmethod
    def _safe_path(root: Path, supplied: str) -> Path:
        if not supplied or "\x00" in supplied:
            raise ValueError("A non-empty file path is required")
        candidate = Path(supplied)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise PermissionError("File tools may only access the workflow workspace") from exc
        return candidate

    @staticmethod
    def _snapshot_files(root: Path) -> dict[str, tuple[int, int]]:
        snapshot: dict[str, tuple[int, int]] = {}
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                stat = path.stat()
                snapshot[path.relative_to(root).as_posix()] = (
                    stat.st_mtime_ns,
                    stat.st_size,
                )
            except OSError:
                continue
        return snapshot

    @staticmethod
    def _changed_files(
        before: dict[str, tuple[int, int]], after: dict[str, tuple[int, int]]
    ) -> list[str]:
        return sorted(name for name, metadata in after.items() if before.get(name) != metadata)

    @staticmethod
    def _load_skill(skill_name: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", skill_name):
            raise ValueError(f"Invalid skill name: {skill_name}")
        path = (Path(SKILLS_DIR) / skill_name / "SKILL.md").resolve()
        try:
            path.relative_to(Path(SKILLS_DIR).resolve())
        except ValueError as exc:
            raise ValueError(f"Invalid skill name: {skill_name}") from exc
        if not path.is_file():
            raise FileNotFoundError(f"Skill not found: {skill_name}")
        return path.read_text(encoding="utf-8")

    async def _run_command(
        self,
        root: Path,
        workflow_id: str,
        command: str,
        timeout: int,
    ) -> str:
        if not command.strip():
            return "Command is empty"
        env = {key: str(value) for key, value in os.environ.items() if value is not None}
        env.setdefault("PYTHONUTF8", "1")
        if os.name == "nt":
            executable = os.path.join(
                os.environ.get("SystemRoot", r"C:\Windows"),
                "System32",
                "WindowsPowerShell",
                "v1.0",
                "powershell.exe",
            )
            args = [
                executable,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ]
        else:
            args = ["/bin/sh", "-lc", command]
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(root),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes.setdefault(workflow_id, set()).add(process)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return f"Command timed out after {timeout}s"
        finally:
            self._processes.get(workflow_id, set()).discard(process)
        output = (stdout + stderr).decode("utf-8", errors="replace")
        output = output[-MAX_TOOL_OUTPUT:]
        return f"exit_code={process.returncode}\n{output}".rstrip()

    async def _execute_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        root: Path,
        workflow_id: str,
    ) -> str:
        aliases = {
            "bash": "run_command",
            "execute_bash": "run_command",
            "write": "write_file",
            "str_replace_editor": "write_file",
        }
        name = aliases.get(name, name)
        if name == "read_file":
            path = self._safe_path(root, str(arguments.get("path", "")))
            if not path.is_file():
                return f"File not found: {path.relative_to(root).as_posix()}"
            text = path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_READ]
            lines = text.splitlines()
            offset = max(0, int(arguments.get("offset", 0)))
            limit = min(2000, max(1, int(arguments.get("limit", 400))))
            selected = lines[offset : offset + limit]
            return "\n".join(
                f"{number:>6}: {line}"
                for number, line in enumerate(selected, start=offset + 1)
            )
        if name == "write_file":
            supplied = arguments.get("path") or arguments.get("file_path")
            path = self._safe_path(root, str(supplied or ""))
            content = arguments.get("content")
            if content is None:
                content = arguments.get("new_content", "")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(content), encoding="utf-8")
            return f"Wrote {len(str(content))} characters to {path.relative_to(root).as_posix()}"
        if name == "replace_in_file":
            path = self._safe_path(root, str(arguments.get("path", "")))
            text = path.read_text(encoding="utf-8")
            old_text = str(arguments.get("old_text", ""))
            if not old_text:
                return "old_text must not be empty"
            count = text.count(old_text)
            if count != 1:
                return f"Expected exactly one match, found {count}"
            path.write_text(
                text.replace(old_text, str(arguments.get("new_text", "")), 1),
                encoding="utf-8",
            )
            return f"Updated {path.relative_to(root).as_posix()}"
        if name == "list_files":
            pattern = str(arguments.get("pattern") or "**/*")
            entries = []
            for path in root.glob(pattern):
                if path.is_file() and ".git" not in path.parts:
                    entries.append(path.relative_to(root).as_posix())
                if len(entries) >= 1000:
                    break
            return "\n".join(sorted(entries)) or "No matching files"
        if name == "search_files":
            query = str(arguments.get("query", ""))
            if not query:
                return "query must not be empty"
            matcher = re.compile(query) if arguments.get("regex") else None
            pattern = str(arguments.get("pattern") or "**/*")
            matches: list[str] = []
            for path in root.glob(pattern):
                if not path.is_file() or ".git" in path.parts or path.stat().st_size > 2_000_000:
                    continue
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except (OSError, UnicodeDecodeError):
                    continue
                for number, line in enumerate(lines, 1):
                    if (matcher.search(line) if matcher else query in line):
                        matches.append(
                            f"{path.relative_to(root).as_posix()}:{number}:{line[:500]}"
                        )
                        if len(matches) >= 500:
                            return "\n".join(matches)
            return "\n".join(matches) or "No matches"
        if name == "run_command":
            return await self._run_command(
                root,
                workflow_id,
                str(arguments.get("command", "")),
                min(1800, max(1, int(arguments.get("timeout", 300)))),
            )
        return f"Unsupported tool: {name}"

    @staticmethod
    def _resolve_claude_executable(configured: str) -> Path | None:
        values = [configured, str(CLAUDE_BIN), "claude"]
        for value in values:
            raw = (value or "").strip().strip('"')
            if not raw:
                continue
            supplied = Path(raw).expanduser()
            candidate = supplied if supplied.is_file() else None
            if candidate is None:
                discovered = shutil.which(raw)
                if discovered:
                    candidate = Path(discovered)
            if candidate is None or not candidate.is_file():
                continue
            if candidate.suffix.lower() in {".cmd", ".bat"}:
                native = (
                    candidate.parent
                    / "node_modules"
                    / "@anthropic-ai"
                    / "claude-code"
                    / "bin"
                    / "claude.exe"
                )
                if native.is_file():
                    candidate = native
            if candidate.suffix.lower() not in {".cmd", ".bat"}:
                return candidate.resolve()
        return None

    async def _run_local_claude(
        self,
        *,
        root: Path,
        workflow_id: str,
        system_prompt: str,
        user_prompt: str,
        settings: dict[str, str],
        cancel_event: asyncio.Event,
        before: dict[str, tuple[int, int]],
        on_output: OutputCallback | None,
        on_delta: OutputCallback | None,
        inactivity_timeout: int,
        resume_session_id: str | None,
    ) -> dict[str, Any]:
        executable = self._resolve_claude_executable(
            settings.get("claude_bin", "claude")
        )
        if executable is None:
            raise FileNotFoundError(
                "Local Claude Code was selected but no compatible executable was found"
            )

        permission_mode = settings.get("claude_permission_mode", "acceptEdits")
        if permission_mode not in {"acceptEdits", "auto", "manual"}:
            permission_mode = "acceptEdits"
        args = [
            str(executable),
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--permission-mode",
            permission_mode,
            "--allowedTools",
            "Read,Write,Edit,Glob,Grep,Bash",
        ]
        effort = settings.get("claude_effort", "high").strip().lower()
        if effort in {"low", "medium", "high", "xhigh", "max"}:
            args.extend(["--effort", effort])
        model = settings.get("claude_model", "").strip()
        if model:
            args.extend(["--model", model])
        if resume_session_id:
            args.extend(["--resume", resume_session_id])

        env = {key: str(value) for key, value in os.environ.items() if value is not None}
        env.setdefault("PYTHONUTF8", "1")
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(root),
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes.setdefault(workflow_id, set()).add(process)
        prompt = f"{system_prompt}\n\nTASK\n{user_prompt}"
        assert process.stdin is not None
        process.stdin.write(prompt.encode("utf-8"))
        await process.stdin.drain()
        process.stdin.close()

        stderr_task = asyncio.create_task(process.stderr.read())
        stream_text = ""
        assistant_text = ""
        result_text = ""
        session_id = resume_session_id or ""
        result_error = False
        partial_seen = False
        try:
            assert process.stdout is not None
            while True:
                if cancel_event.is_set():
                    if process.returncode is None:
                        process.terminate()
                    break
                try:
                    raw_line = await asyncio.wait_for(
                        process.stdout.readline(), timeout=inactivity_timeout
                    )
                except asyncio.TimeoutError as exc:
                    if process.returncode is None:
                        process.terminate()
                    raise RuntimeError(
                        f"Local Claude Code produced no output for {inactivity_timeout}s"
                    ) from exc
                if not raw_line:
                    break
                try:
                    event = json.loads(raw_line.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                session_id = str(event.get("session_id") or session_id)
                event_type = event.get("type")
                if event_type == "stream_event":
                    stream_event = event.get("event") or {}
                    delta = stream_event.get("delta") or {}
                    text = delta.get("text") if isinstance(delta, dict) else None
                    if isinstance(text, str) and text:
                        partial_seen = True
                        stream_text += text
                        await self._emit(on_delta, text)
                    content_block = stream_event.get("content_block") or {}
                    if (
                        stream_event.get("type") == "content_block_start"
                        and isinstance(content_block, dict)
                        and content_block.get("type") == "tool_use"
                    ):
                        await self._emit(
                            on_output, f"\n[tool] {content_block.get('name', 'tool')}\n"
                        )
                elif event_type == "assistant":
                    message = event.get("message") or {}
                    blocks = message.get("content") if isinstance(message, dict) else []
                    texts = [
                        str(block.get("text"))
                        for block in blocks or []
                        if isinstance(block, dict)
                        and block.get("type") == "text"
                        and block.get("text")
                    ]
                    if texts:
                        assistant_text = "".join(texts)
                        if on_delta is not None and not partial_seen:
                            await self._emit(on_delta, assistant_text)
                elif event_type == "result":
                    result_error = bool(event.get("is_error"))
                    if isinstance(event.get("result"), str):
                        result_text = event["result"]

            return_code = await process.wait()
            stderr = (await stderr_task).decode("utf-8", errors="replace").strip()
            final_text = result_text or assistant_text or stream_text
            if cancel_event.is_set():
                return {
                    "success": False,
                    "cancelled": True,
                    "output": final_text,
                    "session_id": session_id,
                    "output_files": self._changed_files(
                        before, self._snapshot_files(root)
                    ),
                }
            if return_code != 0 or result_error:
                raise RuntimeError(
                    stderr[-4000:]
                    or final_text[-4000:]
                    or f"Local Claude Code exited with code {return_code}"
                )
            if on_delta is None:
                await self._emit(on_output, final_text)
            return {
                "success": True,
                "output": final_text,
                "result": final_text,
                "session_id": session_id,
                "output_files": self._changed_files(before, self._snapshot_files(root)),
                "runtime": "local_claude",
            }
        finally:
            if not stderr_task.done():
                stderr_task.cancel()
            self._processes.get(workflow_id, set()).discard(process)

    async def run_skill(
        self,
        skill_name: str,
        arguments: str,
        cwd: str | Path,
        workflow_id: str,
        on_output: OutputCallback | None = None,
        on_delta: OutputCallback | None = None,
        extra_params: dict[str, Any] | None = None,
        workspace_files: list[str] | None = None,
        context_summary: str | None = None,
        inactivity_timeout: int = 2400,
        resume_session_id: str | None = None,
    ) -> dict[str, Any]:
        root = Path(cwd).resolve()
        root.mkdir(parents=True, exist_ok=True)
        if workflow_id in self._cancel_events:
            raise RuntimeError(f"Workflow is already running: {workflow_id}")
        cancel_event = asyncio.Event()
        self._cancel_events[workflow_id] = cancel_event
        self._processes.setdefault(workflow_id, set())
        before = self._snapshot_files(root)
        session_id = resume_session_id or hashlib.sha256(
            f"{workflow_id}:{skill_name}".encode("utf-8")
        ).hexdigest()[:20]

        try:
            skill_text = self._load_skill(skill_name)
            system = (
                "You are the execution runtime for an ArHub skill. Follow the skill "
                "instructions exactly and use tools to inspect or modify the workspace. "
                "The host is Windows. Translate any Bash examples in the skill to "
                "PowerShell before calling run_command. Never claim a file was created "
                "unless you created and verified it. Keep all file operations inside the "
                f"workspace: {root}\n\nSKILL INSTRUCTIONS\n{skill_text}"
            )
            user_parts = [f"Arguments:\n{arguments or '(none)'}"]
            if extra_params:
                user_parts.append(
                    "Additional parameters:\n"
                    + json.dumps(extra_params, ensure_ascii=False, indent=2)
                )
            if workspace_files:
                user_parts.append("Workspace files:\n" + "\n".join(workspace_files[:1000]))
            if context_summary:
                user_parts.append("Previous context:\n" + context_summary[-30_000:])
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ]
            settings = await get_all_settings()
            if settings.get("agent_runtime", "openai_compatible") == "local_claude":
                return await self._run_local_claude(
                    root=root,
                    workflow_id=workflow_id,
                    system_prompt=system,
                    user_prompt="\n\n".join(user_parts),
                    settings=settings,
                    cancel_event=cancel_event,
                    before=before,
                    on_output=on_output,
                    on_delta=on_delta,
                    inactivity_timeout=inactivity_timeout,
                    resume_session_id=resume_session_id,
                )

            final_text = ""
            for round_number in range(1, 41):
                if cancel_event.is_set():
                    return {
                        "success": False,
                        "cancelled": True,
                        "output": final_text,
                        "session_id": session_id,
                        "output_files": self._changed_files(
                            before, self._snapshot_files(root)
                        ),
                    }
                payload = await asyncio.wait_for(
                    chat_completion(
                        "executor",
                        messages,
                        tools=AGENT_TOOLS,
                        tool_choice="auto",
                        timeout=inactivity_timeout,
                        on_delta=on_delta,
                    ),
                    timeout=inactivity_timeout + 5,
                )
                choices = payload.get("choices") or []
                if not choices:
                    raise RuntimeError("Model returned no choices")
                message = choices[0].get("message") or {}
                text = message_text(message)
                if text:
                    final_text = text
                    if on_delta is None:
                        await self._emit(on_output, text)
                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    changed = self._changed_files(before, self._snapshot_files(root))
                    return {
                        "success": True,
                        "output": final_text,
                        "result": final_text,
                        "session_id": session_id,
                        "output_files": changed,
                        "rounds": round_number,
                    }

                messages.append(
                    {
                        "role": "assistant",
                        "content": message.get("content"),
                        "tool_calls": tool_calls,
                    }
                )
                for tool_call in tool_calls:
                    function = tool_call.get("function") or {}
                    name = str(function.get("name", ""))
                    raw_arguments = function.get("arguments") or "{}"
                    try:
                        parsed = (
                            json.loads(raw_arguments)
                            if isinstance(raw_arguments, str)
                            else raw_arguments
                        )
                        if not isinstance(parsed, dict):
                            raise ValueError("arguments must be an object")
                        await self._emit(on_output, f"\n[tool] {name}\n")
                        result = await self._execute_tool(name, parsed, root, workflow_id)
                    except Exception as exc:
                        result = f"Tool error: {type(exc).__name__}: {exc}"
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": str(tool_call.get("id", name)),
                            "content": result[-MAX_TOOL_OUTPUT:],
                        }
                    )
            raise RuntimeError("Agent reached the maximum of 40 model rounds")
        except asyncio.CancelledError:
            cancel_event.set()
            raise
        except Exception as exc:
            log.exception("Skill %s failed for workflow %s", skill_name, workflow_id)
            return {
                "success": False,
                "error": f"{type(exc).__name__}: {exc}",
                "output": "",
                "session_id": session_id,
                "output_files": self._changed_files(before, self._snapshot_files(root)),
            }
        finally:
            self._cancel_events.pop(workflow_id, None)
            self._processes.pop(workflow_id, None)


claude_runner = ClaudeRunner()
