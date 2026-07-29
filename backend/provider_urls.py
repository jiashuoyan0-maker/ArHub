"""URL resolution for OpenAI-compatible providers."""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


_VERSIONED_PATH_SUFFIXES = ("/v1", "/v4", "/api/v1", "/api/paas/v4")


def chat_completions_url(base_url: str) -> str:
    """Return a complete Chat Completions endpoint for a provider URL."""
    value = (base_url or "").strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Base URL must be an absolute HTTP(S) URL")
    if parsed.query or parsed.fragment:
        raise ValueError("Base URL must not contain a query string or fragment")

    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        endpoint_path = path
    elif path.endswith(_VERSIONED_PATH_SUFFIXES):
        endpoint_path = f"{path}/chat/completions"
    else:
        endpoint_path = f"{path}/v1/chat/completions"

    return urlunsplit((parsed.scheme, parsed.netloc, endpoint_path, "", ""))


def models_url(base_url: str) -> str:
    """Return the models endpoint next to the resolved chat endpoint."""
    chat_url = chat_completions_url(base_url)
    return chat_url[: -len("chat/completions")] + "models"
