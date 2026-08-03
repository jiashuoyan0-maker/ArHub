"""Provider-neutral OpenAI-compatible model client used by ArHub agents."""

from __future__ import annotations

import base64
import inspect
import json
import logging
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

try:
    from provider_urls import chat_completions_url, models_url
    from services.state_store import get_all_settings
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.provider_urls import chat_completions_url, models_url
    from backend.services.state_store import get_all_settings

log = logging.getLogger(__name__)

DeltaCallback = Callable[[str], Awaitable[None] | None]

AGENT_KEYS: dict[str, dict[str, str]] = {
    "executor": {
        "base_url": "executor_base_url",
        "api_key": "executor_api_key",
        "model_id": "executor_model_id",
        "provider": "executor_provider",
        "reasoning_effort": "executor_reasoning_effort",
        "request_options": "executor_request_options",
    },
    "reviewer": {
        "base_url": "reviewer_base_url",
        "api_key": "reviewer_api_key",
        "model_id": "reviewer_model_id",
        "provider": "reviewer_provider",
        "reasoning_effort": "reviewer_reasoning_effort",
        "request_options": "reviewer_request_options",
    },
    "editor_ai": {
        "base_url": "editor_ai_base_url",
        "api_key": "editor_ai_api_key",
        "model_id": "editor_ai_model_id",
        "provider": "editor_ai_provider",
        "reasoning_effort": "editor_ai_reasoning_effort",
        "request_options": "editor_ai_request_options",
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
    provider: str
    reasoning_effort: str
    request_options: dict[str, Any]


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


def _parse_request_options(raw: str, agent: str) -> dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"[{agent}] request options must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"[{agent}] request options must be a JSON object")
    reserved = {"model", "messages", "tools", "tool_choice", "stream"}
    blocked = sorted(reserved.intersection(value))
    if blocked:
        raise ValueError(
            f"[{agent}] request options cannot override: {', '.join(blocked)}"
        )
    return value


def detect_provider(base_url: str, model_id: str, configured: str = "auto") -> str:
    selected = (configured or "auto").strip().lower()
    if selected not in {"auto", "deepseek", "glm", "openai", "generic"}:
        raise ValueError(f"Unsupported provider: {configured}")
    if selected != "auto":
        return selected
    marker = f"{base_url} {model_id}".lower()
    if "deepseek" in marker:
        return "deepseek"
    if any(token in marker for token in ("bigmodel", "zhipu", "glm")):
        return "glm"
    if "openai.com" in marker or model_id.lower().startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    return "generic"


def apply_provider_options(body: dict[str, Any], config: AgentConfig) -> None:
    effort = config.reasoning_effort
    if effort not in {"default", "off", "low", "medium", "high", "xhigh", "max"}:
        raise ValueError(f"[{config.agent}] unsupported reasoning effort: {effort}")
    if effort != "default":
        if config.provider == "glm":
            body["thinking"] = {"type": "disabled" if effort == "off" else "enabled"}
        elif config.provider == "openai":
            body["reasoning_effort"] = {
                "off": "none",
                "xhigh": "high",
                "max": "high",
            }.get(effort, effort)
    body.update(config.request_options)


def provider_summary(config: AgentConfig) -> dict[str, Any]:
    if config.provider == "glm":
        reasoning = "toggle"
    elif config.provider == "openai":
        reasoning = "effort"
    elif config.provider == "deepseek":
        reasoning = "model"
    else:
        reasoning = "custom"
    return {
        "provider": config.provider,
        "model_id": config.model_id,
        "reasoning_control": reasoning,
        "reasoning_effort": config.reasoning_effort,
    }


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
    provider = detect_provider(
        base_url, model_id, settings.get(keys["provider"], "auto")
    )
    reasoning_effort = settings.get(keys["reasoning_effort"], "default").strip().lower()
    request_options = _parse_request_options(
        settings.get(keys["request_options"], ""), agent
    )
    return AgentConfig(
        agent,
        base_url,
        api_key,
        model_id,
        extra_headers,
        provider,
        reasoning_effort,
        request_options,
    )


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


def _delta_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    parts: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


async def _emit_delta(callback: DeltaCallback | None, text: str) -> None:
    if callback is None or not text:
        return
    result = callback(text)
    if inspect.isawaitable(result):
        await result


async def _consume_chat_stream(
    response: httpx.Response,
    agent: str,
    on_delta: DeltaCallback,
) -> dict[str, Any]:
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    tool_calls: dict[int, dict[str, Any]] = {}
    role = "assistant"
    finish_reason: Any = None
    usage: Any = None
    raw_lines: list[str] = []
    saw_choice = False

    async for raw_line in response.aiter_lines():
        line = raw_line.strip()
        if not line or line.startswith(":") or line.startswith("event:"):
            continue
        if not line.startswith("data:"):
            raw_lines.append(line)
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            if data == "[DONE]":
                break
            continue
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            log.debug("Ignoring malformed [%s] stream event", agent)
            continue
        if not isinstance(chunk, dict):
            continue
        if chunk.get("usage") is not None:
            usage = chunk["usage"]
        choices = chunk.get("choices")
        if not isinstance(choices, list):
            continue
        for choice in choices:
            if not isinstance(choice, dict) or int(choice.get("index") or 0) != 0:
                continue
            saw_choice = True
            if choice.get("finish_reason") is not None:
                finish_reason = choice["finish_reason"]
            delta = choice.get("delta") or choice.get("message") or {}
            if not isinstance(delta, dict):
                continue
            if isinstance(delta.get("role"), str):
                role = delta["role"]
            text = _delta_text(delta.get("content"))
            if text:
                content_parts.append(text)
                await _emit_delta(on_delta, text)
            reasoning = _delta_text(delta.get("reasoning_content"))
            if reasoning:
                reasoning_parts.append(reasoning)
            streamed_calls = delta.get("tool_calls")
            if not isinstance(streamed_calls, list):
                continue
            for fallback_index, item in enumerate(streamed_calls):
                if not isinstance(item, dict):
                    continue
                try:
                    index = int(item.get("index", fallback_index))
                except (TypeError, ValueError):
                    index = fallback_index
                target = tool_calls.setdefault(
                    index,
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    },
                )
                if isinstance(item.get("id"), str) and item["id"]:
                    target["id"] = item["id"]
                if isinstance(item.get("type"), str) and item["type"]:
                    target["type"] = item["type"]
                function = item.get("function") or {}
                if not isinstance(function, dict):
                    continue
                if isinstance(function.get("name"), str):
                    target["function"]["name"] += function["name"]
                arguments = function.get("arguments")
                if isinstance(arguments, str):
                    target["function"]["arguments"] += arguments

    if not saw_choice and raw_lines:
        try:
            payload = json.loads("\n".join(raw_lines))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"[{agent}] malformed streaming response") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("choices"), list):
            raise RuntimeError(f"[{agent}] response does not contain a choices array")
        choices = payload.get("choices") or []
        if choices and isinstance(choices[0], dict):
            text = message_text(choices[0].get("message") or {})
            await _emit_delta(on_delta, text)
        return payload
    if not saw_choice:
        raise RuntimeError(f"[{agent}] streaming response did not contain a choice")

    message: dict[str, Any] = {
        "role": role,
        "content": "".join(content_parts) or None,
    }
    if reasoning_parts:
        message["reasoning_content"] = "".join(reasoning_parts)
    if tool_calls:
        message["tool_calls"] = [tool_calls[index] for index in sorted(tool_calls)]
    result: dict[str, Any] = {
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ]
    }
    if usage is not None:
        result["usage"] = usage
    return result


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
    on_delta: DeltaCallback | None = None,
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
    if on_delta is not None:
        body["stream"] = True
    apply_provider_options(body, config)

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=timeout, trust_env=True)
    try:
        if on_delta is not None:
            headers = _headers(config)
            headers["Accept"] = "text/event-stream"
            async with client.stream(
                "POST",
                chat_completions_url(config.base_url),
                json=body,
                headers=headers,
                timeout=timeout,
            ) as response:
                if response.is_error:
                    await response.aread()
                    raise RuntimeError(
                        f"[{agent}] HTTP {response.status_code}: {_error_message(response)}"
                    )
                return await _consume_chat_stream(response, agent, on_delta)
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
