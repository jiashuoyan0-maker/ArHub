"""Model provider settings API with masked secret responses."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from models.schemas import AgentCapabilitiesInfo, ClaudeDetectionInfo
    from services.claude_runner import ClaudeRunner
    from services.llm_client import (
        AGENT_KEYS,
        AGENT_KERNELS,
        REASONING_EFFORTS,
        agent_kernel,
        get_agent_config,
        provider_summary,
        test_connection,
    )
    from services.state_store import get_all_settings, save_settings
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.models.schemas import AgentCapabilitiesInfo, ClaudeDetectionInfo
    from backend.services.claude_runner import ClaudeRunner
    from backend.services.llm_client import (
        AGENT_KEYS,
        AGENT_KERNELS,
        REASONING_EFFORTS,
        agent_kernel,
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
for _agent_name in AGENT_KEYS:
    DEFAULT_SETTINGS[f"{_agent_name}_claude_model"] = ""
SENSITIVE_KEYS = {
    key
    for key in DEFAULT_SETTINGS
    if key.endswith("api_key") or key.endswith("token") or key.endswith("secret")
}
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_SETTING_CHOICES = {
    "agent_runtime": AGENT_KERNELS,
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
    _SETTING_CHOICES[f"{_agent_name}_reasoning_effort"] = REASONING_EFFORTS


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
    settings = {**DEFAULT_SETTINGS, **(await get_all_settings())}
    if agent_kernel(settings, agent) == "local_claude":
        detected = await ClaudeRunner.detect_local_claude(settings)
        return {
            "ok": detected["compatible"],
            "message": detected["message"],
            "runtime": "local_claude",
            "executable": detected["recommended"],
        }
    return await test_connection(agent)


@router.get("/providers", response_model=AgentCapabilitiesInfo)
async def provider_status() -> AgentCapabilitiesInfo:
    settings = {**DEFAULT_SETTINGS, **(await get_all_settings())}
    agents: dict[str, Any] = {}
    for agent in AGENT_KEYS:
        kernel = agent_kernel(settings, agent)
        if kernel == "local_claude":
            role_effort = settings.get(f"{agent}_reasoning_effort", "")
            requested = (
                role_effort
                if role_effort
                and (
                    role_effort != "default"
                    or bool(settings.get(f"{agent}_agent_runtime", "").strip())
                )
                else settings.get("claude_effort", "default")
            )
            effective = "default" if requested in {"default", "off"} else requested
            agents[agent] = {
                "configured": True,
                "kernel": kernel,
                "model_id": settings.get(f"{agent}_claude_model")
                or settings.get("claude_model", ""),
                "reasoning_control": "effort",
                "reasoning_effort": requested,
                "reasoning": {
                    "requested": requested,
                    "effective": effective,
                    "control": "effort",
                    "supported_values": [
                        "default",
                        "low",
                        "medium",
                        "high",
                        "xhigh",
                        "max",
                    ],
                    "downgraded": requested == "off",
                    "message": (
                        "Claude Code does not expose an off value; using its default effort."
                        if requested == "off"
                        else None
                    ),
                },
            }
            continue
        try:
            agents[agent] = {
                "configured": True,
                "kernel": kernel,
                **provider_summary(await get_agent_config(agent)),
            }
        except (RuntimeError, ValueError) as exc:
            agents[agent] = {
                "configured": False,
                "kernel": kernel,
                "message": str(exc),
            }
    return AgentCapabilitiesInfo(
        agents=agents,
        kernels={
            "openai_compatible": {
                "requires": ["base_url", "model_id"],
                "providers": ["auto", "deepseek", "glm", "openai", "generic"],
            },
            "local_claude": {
                "requires": ["compatible_claude_code"],
                "detection_endpoint": "/api/settings/detect-claude",
            },
        },
    )


@router.get("/detect-claude", response_model=ClaudeDetectionInfo)
async def detect_claude() -> ClaudeDetectionInfo:
    """Detect usable local and bundled Claude Code executables."""
    settings = {**DEFAULT_SETTINGS, **(await get_all_settings())}
    return ClaudeDetectionInfo.model_validate(
        await ClaudeRunner.detect_local_claude(settings)
    )
