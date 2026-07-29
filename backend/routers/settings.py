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
    from services.llm_client import AGENT_KEYS, test_connection
    from services.state_store import get_all_settings, save_settings
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import CLAUDE_BIN
    from backend.services.llm_client import AGENT_KEYS, test_connection
    from backend.services.state_store import get_all_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULT_SETTINGS: dict[str, str] = {
    "executor_base_url": "",
    "executor_api_key": "",
    "executor_model_id": "",
    "reviewer_base_url": "",
    "reviewer_api_key": "",
    "reviewer_model_id": "",
    "editor_ai_base_url": "",
    "editor_ai_api_key": "",
    "editor_ai_model_id": "",
    "minimax_api_key": "",
    "minimax_group_id": "",
    "gemini_api_key": "",
    "gpt_image_api_key": "",
    "gpt_image_base_url": "",
    "claude_bin": "claude",
}
SENSITIVE_KEYS = {
    key
    for key in DEFAULT_SETTINGS
    if key.endswith("api_key") or key.endswith("token") or key.endswith("secret")
}
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")


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


@router.get("/detect-claude")
async def detect_claude() -> dict[str, Any]:
    """Legacy compatibility endpoint; the open runtime does not require Claude CLI."""
    candidates: list[str] = []
    configured = Path(CLAUDE_BIN)
    if configured.is_file():
        candidates.append(str(configured))
    discovered = shutil.which("claude")
    if discovered and discovered not in candidates:
        candidates.append(discovered)
    details = [{"path": path, "version": await _version(path)} for path in candidates]
    return {
        "recommended": candidates[0] if candidates else None,
        "candidates": details,
        "required": False,
        "message": "ArHub's open Agent runtime does not require Claude CLI.",
    }
