"""Model provider settings API with masked secret responses."""

from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from config import CLAUDE_BIN
    from services.llm_client import (
        AGENT_KEYS,
        get_agent_config,
        provider_summary,
        test_connection,
    )
    from services.state_store import get_all_settings, save_settings
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import CLAUDE_BIN
    from backend.services.llm_client import (
        AGENT_KEYS,
        get_agent_config,
        provider_summary,
        test_connection,
    )
    from backend.services.state_store import get_all_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULT_SETTINGS: dict[str, str] = {
    "executor_base_url": "",
    "executor_api_key": "",
    "executor_model_id": "",
    "executor_provider": "auto",
    "executor_reasoning_effort": "default",
    "executor_request_options": "",
    "reviewer_base_url": "",
    "reviewer_api_key": "",
    "reviewer_model_id": "",
    "reviewer_provider": "auto",
    "reviewer_reasoning_effort": "default",
    "reviewer_request_options": "",
    "editor_ai_base_url": "",
    "editor_ai_api_key": "",
    "editor_ai_model_id": "",
    "editor_ai_provider": "auto",
    "editor_ai_reasoning_effort": "default",
    "editor_ai_request_options": "",
    "minimax_api_key": "",
    "minimax_group_id": "",
    "gemini_api_key": "",
    "gpt_image_api_key": "",
    "gpt_image_base_url": "",
    "agent_runtime": "openai_compatible",
    "claude_bin": "claude",
    "claude_model": "",
    "claude_effort": "high",
    "claude_permission_mode": "acceptEdits",
}
SENSITIVE_KEYS = {
    key
    for key in DEFAULT_SETTINGS
    if key.endswith("api_key") or key.endswith("token") or key.endswith("secret")
}
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_SETTING_CHOICES = {
    "agent_runtime": {"openai_compatible", "local_claude"},
    "claude_effort": {"default", "low", "medium", "high", "xhigh", "max"},
    "claude_permission_mode": {"acceptEdits", "auto", "manual"},
}
for _agent_name in AGENT_KEYS:
    _SETTING_CHOICES[f"{_agent_name}_provider"] = {
        "auto",
        "deepseek",
        "glm",
        "openai",
        "generic",
    }
    _SETTING_CHOICES[f"{_agent_name}_reasoning_effort"] = {
        "default",
        "off",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    }


class SettingsUpdate(BaseModel):
    settings: dict[str, str] = Field(default_factory=dict)


def mask_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:3] + "*" * min(12, len(value) - 7) + value[-4:]


async def get_settings() -> dict[str, dict[str, str]]:
    stored = await get_all_settings()
    merged = {**DEFAULT_SETTINGS, **stored}
    masked = {
        key: mask_value(value) if key in SENSITIVE_KEYS or key.endswith("api_key") else value
        for key, value in merged.items()
    }
    return {"settings": masked}


@router.get("")
async def get_settings_endpoint() -> dict[str, dict[str, str]]:
    return await get_settings()


@router.put("")
async def update_settings(body: SettingsUpdate) -> dict[str, Any]:
    cleaned: dict[str, str] = {}
    for key, value in body.settings.items():
        if not _KEY_RE.fullmatch(key):
            raise HTTPException(status_code=400, detail=f"Invalid setting key: {key}")
        if len(value) > 200_000:
            raise HTTPException(status_code=400, detail=f"Setting is too large: {key}")
        choices = _SETTING_CHOICES.get(key)
        if choices is not None and value not in choices:
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}: {value}")
        if "*" in value and (key in SENSITIVE_KEYS or key.endswith("api_key")):
            continue
        cleaned[key] = value
    await save_settings(cleaned)
    return {"status": "ok", "saved": len(cleaned)}


@router.post("/test/{agent}")
async def test_agent_connection(agent: str) -> dict[str, Any]:
    if agent not in AGENT_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent}")
    return await test_connection(agent)


@router.get("/providers")
async def provider_status() -> dict[str, Any]:
    agents: dict[str, Any] = {}
    for agent in AGENT_KEYS:
        try:
            agents[agent] = {"configured": True, **provider_summary(await get_agent_config(agent))}
        except (RuntimeError, ValueError) as exc:
            agents[agent] = {"configured": False, "message": str(exc)}
    return {"agents": agents}


async def _version(path: str) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            path,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await asyncio.wait_for(process.communicate(), timeout=5)
        return output.decode("utf-8", errors="replace").strip()[:200]
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}"


def _resolved_claude_path(value: str) -> str | None:
    raw = (value or "").strip().strip('"')
    if not raw:
        return None
    supplied = Path(raw).expanduser()
    candidate = supplied if supplied.is_file() else None
    if candidate is None:
        discovered = shutil.which(raw)
        if discovered:
            candidate = Path(discovered)
    if candidate is None or not candidate.is_file():
        return None
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
    return str(candidate.resolve())


@router.get("/detect-claude")
async def detect_claude() -> dict[str, Any]:
    """Detect usable local and bundled Claude Code executables."""
    settings = {**DEFAULT_SETTINGS, **(await get_all_settings())}
    candidates: list[str] = []
    for value in (settings.get("claude_bin", "claude"), str(CLAUDE_BIN), "claude"):
        resolved = _resolved_claude_path(value)
        if resolved and resolved.casefold() not in {item.casefold() for item in candidates}:
            candidates.append(resolved)
    details = [{"path": path, "version": await _version(path)} for path in candidates]
    return {
        "recommended": candidates[0] if candidates else None,
        "candidates": details,
        "required": False,
        "selected_runtime": settings["agent_runtime"],
        "compatible": bool(candidates),
        "message": (
            "Local Claude Code is ready."
            if candidates
            else "No local Claude Code executable was detected; use the open model runtime."
        ),
    }
