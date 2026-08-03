"""Safe built-in extension actions for the ArHub Studio workspace.

Manifest files describe available views and actions. This router only executes a
small, explicit set of built-in handlers; user-supplied manifests can never
execute Python, shell commands, or browser code through the registry.
"""

from __future__ import annotations

import re
from html import escape as escape_html
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from extension_registry import ExtensionRegistry
    from routers.artifacts import _artifact_item, _safe_path, _workspace
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.extension_registry import ExtensionRegistry
    from backend.routers.artifacts import _artifact_item, _safe_path, _workspace


router = APIRouter(tags=["extensions"])
_registry: ExtensionRegistry | None = None


class ExtensionActionRequest(BaseModel):
    title: str = ""
    description: str = ""


def configure(registry: ExtensionRegistry) -> None:
    """Inject the app-owned registry without importing the FastAPI entry point."""
    global _registry
    _registry = registry


def _slug(value: str, fallback: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return compact[:48] or fallback


def _next_available(path: Path, *, is_dir: bool = False) -> Path:
    if not path.exists():
        return path
    stem = path.name if is_dir else path.stem
    suffix = "" if is_dir else path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise HTTPException(status_code=409, detail="Too many artifacts with the same name")


def _mermaid_label(value: str) -> str:
    return re.sub(r"[\[\]\"\\]", " ", value).strip()[:72] or "Untitled"


def _diagram_source(title: str, description: str) -> str:
    subject = _mermaid_label(title)
    detail = _mermaid_label(description) if description else "梳理关键步骤"
    return (
        "flowchart TD\n"
        "  A[开始] --> B[明确目标]\n"
        f"  B --> C[{subject}]\n"
        f"  C --> D[{detail}]\n"
        "  D --> E[复核与交付]\n"
    )


def _diagram_svg(title: str, description: str) -> str:
    labels = ["开始", "明确目标", title.strip() or "未命名流程", description.strip() or "梳理关键步骤", "复核与交付"]
    rows: list[str] = []
    for index, label in enumerate(labels):
        y = 26 + index * 86
        text = escape_html(label[:52])
        rows.append(
            f'<rect x="58" y="{y}" width="404" height="52" rx="14" fill="#f8fbff" stroke="#0a84ff" stroke-width="2"/>'
            f'<text x="260" y="{y + 32}" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="16" fill="#1d1d1f">{text}</text>'
        )
        if index < len(labels) - 1:
            arrow_y = y + 52
            rows.append(
                f'<path d="M260 {arrow_y} V{arrow_y + 29}" stroke="#5ac8fa" stroke-width="3" marker-end="url(#arrow)"/>'
            )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="470" viewBox="0 0 520 470" role="img" aria-label="Flowchart preview">'
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#5ac8fa"/></marker></defs>'
        '<rect width="520" height="470" rx="22" fill="#eef5ff"/>'
        + "".join(rows)
        + "</svg>"
    )


def _create_diagram(workspace: Path, workflow_id: str, request: ExtensionActionRequest) -> dict[str, Any]:
    title = request.title.strip()[:120] or "新流程图"
    description = request.description.strip()[:600]
    diagrams_dir = workspace / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    base = _slug(title, "flowchart")
    source_path = _next_available(diagrams_dir / f"{base}.mmd")
    preview_path = source_path.with_suffix(".svg")
    source_path.write_text(_diagram_source(title, description), encoding="utf-8")
    preview_path.write_text(_diagram_svg(title, description), encoding="utf-8")
    return {
        "protocol": "arhub.artifact-set.v1",
        "extension_id": "arhub.diagram",
        "action": "create",
        "artifacts": [
            _artifact_item(workspace, source_path),
            _artifact_item(workspace, preview_path),
        ],
        "preview_url": (
            f"/api/workflows/{workflow_id}/extensions/arhub.diagram/preview/"
            f"{quote(preview_path.relative_to(workspace).as_posix(), safe='/')}"
        ),
        "primary_artifact": preview_path.relative_to(workspace).as_posix(),
    }


def _create_web_project(workspace: Path, workflow_id: str, request: ExtensionActionRequest) -> dict[str, Any]:
    title = request.title.strip()[:120] or "ArHub 网页项目"
    description = request.description.strip()[:1200] or "一个由 ArHub Studio 创建的本地网页项目。"
    web_root = workspace / "web"
    web_root.mkdir(parents=True, exist_ok=True)
    project_dir = _next_available(web_root / _slug(title, "site"), is_dir=True)
    project_dir.mkdir(parents=True)
    escaped_title = escape_html(title)
    escaped_description = escape_html(description)
    (project_dir / "index.html").write_text(
        "<!doctype html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>{escaped_title}</title><link rel=\"stylesheet\" href=\"styles.css\"></head>\n"
        "<body><main class=\"site-shell\"><p class=\"eyebrow\">ArHub Web Studio</p>\n"
        f"<h1>{escaped_title}</h1><p class=\"summary\">{escaped_description}</p>\n"
        "<button id=\"action\" type=\"button\">开始探索</button><p id=\"status\" aria-live=\"polite\"></p>\n"
        "</main><script src=\"app.js\"></script></body></html>\n",
        encoding="utf-8",
    )
    (project_dir / "styles.css").write_text(
        ":root { color-scheme: light dark; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }\n"
        "body { min-height: 100vh; margin: 0; display: grid; place-items: center; color: #1d1d1f; background: linear-gradient(135deg, #edf5ff, #fff5fb); }\n"
        ".site-shell { width: min(680px, calc(100% - 48px)); padding: 48px; border: 1px solid rgba(255,255,255,.8); border-radius: 24px; background: rgba(255,255,255,.74); box-shadow: 0 24px 64px rgba(10,132,255,.16); backdrop-filter: blur(24px) saturate(150%); }\n"
        ".eyebrow { color: #007aff; font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; } h1 { font-size: clamp(2rem, 7vw, 4rem); margin: .2em 0; } .summary { font-size: 1.1rem; line-height: 1.7; color: #51545b; }\n"
        "button { min-height: 44px; padding: 0 20px; border: 0; border-radius: 999px; color: white; background: #007aff; font: inherit; font-weight: 650; cursor: pointer; } button:active { transform: scale(.98); }\n",
        encoding="utf-8",
    )
    (project_dir / "app.js").write_text(
        "const button = document.querySelector('#action');\n"
        "const status = document.querySelector('#status');\n"
        "button?.addEventListener('click', () => { status.textContent = '网页交互已启动。'; });\n",
        encoding="utf-8",
    )
    index_path = project_dir / "index.html"
    return {
        "protocol": "arhub.artifact-set.v1",
        "extension_id": "arhub.web",
        "action": "create",
        "artifacts": [
            _artifact_item(workspace, index_path),
            _artifact_item(workspace, project_dir / "styles.css"),
            _artifact_item(workspace, project_dir / "app.js"),
        ],
        "preview_url": (
            f"/api/workflows/{workflow_id}/extensions/arhub.web/preview/"
            f"{quote(index_path.relative_to(workspace).as_posix(), safe='/')}"
        ),
        "primary_artifact": index_path.relative_to(workspace).as_posix(),
    }


BUILTIN_HANDLERS = {
    "builtin.diagram.create": _create_diagram,
    "builtin.web.create": _create_web_project,
}


def _snapshot() -> dict[str, Any]:
    if _registry is None:
        raise HTTPException(status_code=503, detail="Extension registry is not ready")
    snapshot = _registry.snapshot()
    for action in snapshot.get("actions", []):
        action["enabled"] = (
            action.get("source") == "builtin"
            and action.get("handler") in BUILTIN_HANDLERS
        )
    return snapshot


@router.get("/api/workflows/{workflow_id}/extensions")
async def workflow_extensions(workflow_id: str) -> dict[str, Any]:
    await _workspace(workflow_id)
    return _snapshot()


@router.post("/api/workflows/{workflow_id}/extensions/{extension_id}/actions/{action_id}")
async def run_extension_action(
    workflow_id: str,
    extension_id: str,
    action_id: str,
    request: ExtensionActionRequest,
) -> dict[str, Any]:
    snapshot = _snapshot()
    action = next(
        (
            item
            for item in snapshot.get("actions", [])
            if item.get("extension_id") == extension_id
            and item.get("local_id") == action_id
        ),
        None,
    )
    if action is None:
        raise HTTPException(status_code=404, detail="Extension action was not found")
    if not action.get("enabled"):
        raise HTTPException(status_code=403, detail="Extension action is not enabled")
    handler = BUILTIN_HANDLERS.get(str(action.get("handler") or ""))
    if handler is None:
        raise HTTPException(status_code=404, detail="No built-in handler is registered")
    workspace = await _workspace(workflow_id)
    return handler(workspace, workflow_id, request)


def _preview_file(workspace: Path, relative_path: str, root_name: str) -> Path:
    target = _safe_path(workspace, relative_path)
    allowed_root = (workspace / root_name).resolve()
    try:
        target.relative_to(allowed_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Preview path is outside its extension workspace") from exc
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Preview file was not found")
    return target


@router.get("/api/workflows/{workflow_id}/extensions/arhub.diagram/preview/{path:path}")
async def diagram_preview(workflow_id: str, path: str) -> FileResponse:
    workspace = await _workspace(workflow_id)
    target = _preview_file(workspace, path, "diagrams")
    if target.suffix.lower() != ".svg":
        raise HTTPException(status_code=415, detail="Only SVG diagram previews are supported")
    return FileResponse(target, media_type="image/svg+xml")


@router.get("/api/workflows/{workflow_id}/extensions/arhub.web/preview/{path:path}")
async def web_preview(workflow_id: str, path: str) -> FileResponse:
    workspace = await _workspace(workflow_id)
    target = _preview_file(workspace, path, "web")
    if target.suffix.lower() not in {".html", ".htm", ".css", ".js", ".json", ".svg", ".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=415, detail="This file type cannot be served in web preview")
    return FileResponse(target)
