"""Provider-neutral lightweight editing support for the workspace editor."""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any

try:
    from services.llm_client import call_llm as provider_call_llm
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.services.llm_client import call_llm as provider_call_llm


LATEX_SYSTEM_PROMPT = """You are a precise LaTeX editor. Preserve valid project
structure, commands, citations, and surrounding prose. Return only the JSON object
requested by the host."""

MARKDOWN_SYSTEM_PROMPT = """You are a precise Markdown and Word-source editor.
Preserve Markdown structure. Use PNG images and Markdown-compatible math and
citations. Return only the JSON object requested by the host."""

PYTHON_SYSTEM_PROMPT = """You are a precise Python editor. Preserve the existing
project conventions and return complete runnable file content. Return only the JSON
object requested by the host."""

REPLY_FORMAT = """Return one JSON object with this shape:
{
  "summary": "short description or direct answer",
  "target_file": "relative/path.ext",
  "modified_content": "complete replacement content",
  "multi_edit": [{"path": "relative/path.ext", "content": "complete content"}]
}
Use modified_content for one file and multi_edit for multiple files. For a question
that requires no file change, omit modified_content and multi_edit and answer in
summary. Never wrap the JSON in a Markdown code fence."""

_PROMPTS = {
    "latex": LATEX_SYSTEM_PROMPT,
    "markdown": MARKDOWN_SYSTEM_PROMPT,
    "python": PYTHON_SYSTEM_PROMPT,
}


def _clean_path(value: Any, fallback: str = "") -> str:
    text = str(value or fallback).replace("\\", "/").strip()
    path = PurePosixPath(text)
    if not text or path.is_absolute() or ".." in path.parts:
        return fallback
    return path.as_posix()


def _extract_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    candidates = [stripped]
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", stripped, re.I)
    if fenced:
        candidates.append(fenced.group(1))
    start = stripped.find("{")
    end = stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _normalize_reply(
    raw: dict[str, Any], current_file: str, current_content: str
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "summary": str(raw.get("summary") or raw.get("message") or "").strip()
    }
    multi_edit = raw.get("multi_edit") or raw.get("edits")
    normalized_edits: list[dict[str, str]] = []
    if isinstance(multi_edit, list):
        for item in multi_edit:
            if not isinstance(item, dict):
                continue
            path = _clean_path(item.get("path") or item.get("file"))
            content = item.get("content", item.get("modified_content"))
            if path and isinstance(content, str):
                normalized_edits.append({"path": path, "content": content})
    if normalized_edits:
        result["multi_edit"] = normalized_edits
        if len(normalized_edits) == 1:
            result["target_file"] = normalized_edits[0]["path"]
            result["modified_content"] = normalized_edits[0]["content"]
        return result

    content = raw.get("modified_content", raw.get("content"))
    if isinstance(content, str):
        target = _clean_path(raw.get("target_file") or raw.get("path"), current_file)
        result["target_file"] = target or current_file
        result["modified_content"] = content
    elif not result["summary"]:
        result["summary"] = "The model did not return an editable response."
    return result


async def call_llm(agent: str, prompt: str, timeout: int = 300) -> str:
    """Call the configured OpenAI-compatible provider for an editor role."""

    return await provider_call_llm(agent, prompt, timeout=timeout)


async def ai_edit(
    message: str,
    current_file: str,
    current_content: str,
    workspace_files: list[str],
    compile_log: str = "",
    extra_context: str = "",
    history: list[dict[str, Any]] | None = None,
    role: str = "latex",
    chat_summary: str = "",
) -> dict[str, Any]:
    """Ask the configured editor model for a structured file edit."""

    selected_role = role if role in _PROMPTS else "latex"
    recent_history = []
    for item in (history or [])[-10:]:
        if isinstance(item, dict) and item.get("role") in {"user", "ai", "system"}:
            recent_history.append(
                {
                    "role": item.get("role"),
                    "content": str(item.get("content", ""))[-4000:],
                }
            )
    prompt = "\n\n".join(
        part
        for part in [
            _PROMPTS[selected_role],
            REPLY_FORMAT,
            f"User instruction:\n{message}",
            f"Current file: {current_file or '(none)'}",
            f"Current file content:\n{current_content}",
            "Workspace files:\n" + "\n".join(workspace_files[:1000]),
            f"Compile or runtime log:\n{compile_log[-20_000:]}" if compile_log else "",
            f"Referenced file context:\n{extra_context[-50_000:]}" if extra_context else "",
            f"Previous chat summary:\n{chat_summary[-10_000:]}" if chat_summary else "",
            "Recent chat:\n" + json.dumps(recent_history, ensure_ascii=False)
            if recent_history
            else "",
        ]
        if part
    )
    response = await call_llm("editor_ai", prompt, timeout=300)
    parsed = _extract_json(response)
    if parsed is None:
        return {"summary": response.strip() or "The model returned an empty response."}
    return _normalize_reply(parsed, current_file, current_content)
