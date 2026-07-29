"""Provider-neutral OpenAI-compatible model client used by ArHub agents."""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

try:
    from provider_urls import chat_completions_url, models_url
    from services.state_store import get_all_settings
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.provider_urls import chat_completions_url, models_url
    from backend.services.state_store import get_all_settings

log = logging.getLogger(__name__)

AGENT_KEYS: dict[str, dict[str, str]] = {
    "executor": {
        "base_url": "executor_base_url",
        "api_key": "executor_api_key",
        "model_id": "executor_model_id",
    },
    "reviewer": {
        "base_url": "reviewer_base_url",
        "api_key": "reviewer_api_key",
        "model_id": "reviewer_model_id",
    },
    "editor_ai": {
        "base_url": "editor_ai_base_url",
        "api_key": "editor_ai_api_key",
        "model_id": "editor_ai_model_id",
    },
}

ENV_MAPPING = {
    "executor_base_url": "OPENAI_BASE_URL",
    "executor_api_key": "OPENAI_API_KEY",
    "executor_model_id": "OPENAI_MODEL",
    "reviewer_base_url": "REVIEWER_BASE_URL",
    "reviewer_api_key": "REVIEWER_API_KEY",
    "reviewer_model_id": "REVIEWER_MODEL",
    "editor_ai_base_url": "EDITOR_AI_BASE_URL",
    "editor_ai_api_key": "EDITOR_AI_API_KEY",
    "editor_ai_model_id": "EDITOR_AI_MODEL",
    "gpt_image_base_url": "GPT_IMAGE_BASE_URL",
    "gpt_image_api_key": "GPT_IMAGE_API_KEY",
}


@dataclass(frozen=True)
class AgentConfig:
    agent: str
    base_url: str
    api_key: str
    model_id: str
    extra_headers: dict[str, str]


def _parse_extra_headers(raw: str, agent: str) -> dict[str, str]:
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"[{agent}] extra headers must be valid JSON") from exc
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError(f"[{agent}] extra headers must be a string-to-string object")
    return value


async def get_agent_config(agent: str) -> AgentConfig:
    if agent not in AGENT_KEYS:
        raise ValueError(f"Unknown agent: {agent}")
    settings = await get_all_settings()
    keys = AGENT_KEYS[agent]
    base_url = settings.get(keys["base_url"], "").strip()
    api_key = settings.get(keys["api_key"], "").strip()
    model_id = settings.get(keys["model_id"], "").strip()
    if not base_url:
        raise RuntimeError(f"[{agent}] Base URL is not configured")
    if not model_id:
        raise RuntimeError(f"[{agent}] Model ID is not configured")
    extra_headers = _parse_extra_headers(
        settings.get(f"{agent}_extra_headers", ""), agent
    )
    return AgentConfig(agent, base_url, api_key, model_id, extra_headers)


def _headers(config: AgentConfig) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    headers.update(config.extra_headers)
    return headers


def _error_message(response: httpx.Response) -> str:
    text = response.text.strip().replace("\x00", "")
    try:
        payload = response.json()
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and error.get("message"):
                text = str(error["message"])
            elif isinstance(error, str):
                text = error
            elif payload.get("message"):
                text = str(payload["message"])
    except (ValueError, json.JSONDecodeError):
        pass
    return text[:800] or response.reason_phrase


async def chat_completion(
    agent: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
    timeout: float = 300,
    max_tokens: int | None = None,
    temperature: float | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Send a chat-completions request and return the provider response."""
    config = await get_agent_config(agent)
    body: dict[str, Any] = {"model": config.model_id, "messages": messages}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice or "auto"
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if temperature is not None:
        body["temperature"] = temperature

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=timeout, trust_env=True)
    try:
        response = await client.post(
            chat_completions_url(config.base_url),
            json=body,
            headers=_headers(config),
            timeout=timeout,
        )
        if response.is_error:
            raise RuntimeError(
                f"[{agent}] HTTP {response.status_code}: {_error_message(response)}"
            )
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("choices"), list):
            raise RuntimeError(f"[{agent}] response does not contain a choices array")
        return payload
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"[{agent}] request timed out after {timeout:g}s") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"[{agent}] connection failed: {type(exc).__name__}: {exc}") from exc
    finally:
        if owns_client:
            await client.aclose()


def message_text(message: dict[str, Any]) -> str:
    """Normalize text content returned by common OpenAI-compatible providers."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "\n".join(parts)
    reasoning = message.get("reasoning_content")
    return reasoning if isinstance(reasoning, str) else ""


async def call_llm(agent: str, prompt: str, timeout: int = 300) -> str:
    payload = await chat_completion(
        agent, [{"role": "user", "content": prompt}], timeout=timeout
    )
    choices = payload.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        raise RuntimeError(f"[{agent}] model returned no choices")
    message = choices[0].get("message") or {}
    return message_text(message)


async def describe_image(image_path: str, context: str = "") -> str:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    content: list[dict[str, Any]] = []
    if context:
        content.append({"type": "text", "text": context})
    content.append(
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
        }
    )
    payload = await chat_completion(
        "editor_ai",
        [{"role": "user", "content": content}],
        timeout=120,
        max_tokens=1200,
    )
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("[editor_ai] model returned no choices")
    return message_text(choices[0].get("message") or {})


async def test_connection(agent: str) -> dict[str, Any]:
    try:
        config = await get_agent_config(agent)
        payload = await chat_completion(
            agent,
            [{"role": "user", "content": "Reply with OK."}],
            timeout=20,
            max_tokens=8,
        )
        if payload.get("choices"):
            return {
                "ok": True,
                "message": f"Connected to {config.model_id}",
                "endpoint": chat_completions_url(config.base_url),
            }
    except Exception as chat_error:
        try:
            config = await get_agent_config(agent)
            async with httpx.AsyncClient(timeout=15, trust_env=True) as client:
                response = await client.get(
                    models_url(config.base_url), headers=_headers(config)
                )
                if not response.is_error:
                    return {
                        "ok": True,
                        "message": f"Connected to model registry for {config.model_id}",
                        "endpoint": models_url(config.base_url),
                    }
        except Exception:
            pass
        return {"ok": False, "message": str(chat_error)}
    return {"ok": False, "message": f"[{agent}] model returned no choices"}


async def get_env_for_subprocess() -> dict[str, str]:
    settings = await get_all_settings()
    env = {key: str(value) for key, value in os.environ.items() if value is not None}
    for setting_key, env_key in ENV_MAPPING.items():
        value = settings.get(setting_key)
        if value is not None:
            env[env_key] = str(value)
    claude_bin = settings.get("claude_bin")
    if claude_bin:
        env["CLAUDE_BIN"] = str(claude_bin)
    env.setdefault("PYTHONUTF8", "1")
    return env
