"""Workspace artifact browsing, upload, editing and export."""

from __future__ import annotations

import io
import json
import mimetypes
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

try:
    from config import WORKSPACES_DIR
    from services.extract_worker import get_status, schedule_extract
    from services.state_store import get_db, get_workflow, update_workflow
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import WORKSPACES_DIR
    from backend.services.extract_worker import get_status, schedule_extract
    from backend.services.state_store import get_db, get_workflow, update_workflow

router = APIRouter(tags=["artifacts"])

TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".htm",
    ".tex",
    ".bib",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".json",
    ".xml",
    ".drawio",
    ".log",
    ".sh",
    ".ps1",
    ".bat",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}


class ArtifactUpdate(BaseModel):
    content: str


async def _workspace(workflow_id: str) -> Path:
    db = await get_db()
    try:
        workflow = await get_workflow(db, workflow_id)
        if workflow is None:
            raise HTTPException(status_code=404, detail="Workflow not found")

        workspace = Path(workflow.get("workspace_dir") or "").resolve()
        root = Path(WORKSPACES_DIR).resolve()
        try:
            workspace.relative_to(root)
        except ValueError as exc:
            migrated = (root / workflow_id).resolve()
            try:
                migrated.relative_to(root)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid workflow workspace"
                ) from exc
            if not migrated.is_dir():
                raise HTTPException(
                    status_code=400, detail="Invalid workflow workspace"
                ) from exc
            workspace = migrated
            await update_workflow(db, workflow_id, workspace_dir=str(workspace))

        workspace.mkdir(parents=True, exist_ok=True)
        return workspace
    finally:
        await db.close()


def _safe_path(workspace: Path, supplied: str, *, allow_root: bool = False) -> Path:
    candidate = (workspace / supplied).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Artifact path leaves the workspace") from exc
    if candidate == workspace and not allow_root:
        raise HTTPException(status_code=400, detail="Artifact path is empty")
    return candidate


def _artifact_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".pdf":
        return "pdf"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix == ".json":
        return "json"
    if suffix in TEXT_SUFFIXES:
        return "text"
    return "binary"


def _artifact_item(workspace: Path, path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": path.relative_to(workspace).as_posix(),
        "name": path.name,
        "type": _artifact_type(path),
        "size": stat.st_size,
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat(),
    }


@router.get("/api/workflows/{wf_id}/artifacts")
async def list_artifacts(wf_id: str) -> list[dict[str, Any]]:
    workspace = await _workspace(wf_id)
    result = []
    for path in workspace.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            result.append(_artifact_item(workspace, path))
        except OSError:
            continue
    return sorted(result, key=lambda item: item["path"].lower())


@router.get("/api/workflows/{wf_id}/artifacts/extract-status")
async def extract_status(
    wf_id: str, target_dir: str = "user_data"
) -> dict[str, Any]:
    workspace = await _workspace(wf_id)
    target = _safe_path(workspace, target_dir, allow_root=True)
    target.mkdir(parents=True, exist_ok=True)
    status = get_status(target)
    known = status.get("files") if isinstance(status.get("files"), dict) else {}
    for path in target.iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in {".pdf", ".docx", ".doc"}
            and path.name not in known
        ):
            schedule_extract(target, path.name, _extract_uploaded_file)
    return get_status(target)


@router.get("/api/workflows/{wf_id}/artifacts/export")
async def export_workspace(wf_id: str) -> StreamingResponse:
    workspace = await _workspace(wf_id)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in workspace.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                archive.write(path, path.relative_to(workspace).as_posix())
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(f'ArHub_{wf_id}_workspace.zip')}"
        },
    )


@router.post("/api/workflows/{wf_id}/artifacts/upload")
async def upload_files(
    wf_id: str,
    files: list[UploadFile] = File(...),
    target_dir: str | None = "user_data",
) -> dict[str, Any]:
    workspace = await _workspace(wf_id)
    target = _safe_path(workspace, target_dir or "", allow_root=True)
    target.mkdir(parents=True, exist_ok=True)
    saved = []
    for upload in files:
        filename = Path(upload.filename or "upload.bin").name
        if not filename or filename in {".", ".."}:
            raise HTTPException(status_code=400, detail="Invalid upload filename")
        destination = _safe_path(workspace, str((target / filename).relative_to(workspace)))
        size = 0
        with destination.open("wb") as stream:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > 2_000_000_000:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=f"File is too large: {filename}")
                stream.write(chunk)
        saved.append(_artifact_item(workspace, destination))
        if destination.suffix.lower() in {".pdf", ".docx", ".doc"}:
            schedule_extract(target, filename, _extract_uploaded_file)
    return {"saved": saved, "count": len(saved)}


def _extract_text(filename: str, raw: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return raw.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        from docx import Document

        document = Document(io.BytesIO(raw))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    return f"Source file: {filename}\n\n(Binary content retained in user_data.)"


def _extract_uploaded_file(
    source: Path, _previous: Path | None = None
) -> tuple[str, dict[str, Any]]:
    """Extract searchable UTF-8 text without mutating the uploaded source."""

    raw = source.read_bytes()
    text = _extract_text(source.name, raw)
    return text, {
        "source_size": len(raw),
        "source_mtime_ns": source.stat().st_mtime_ns,
        "extracted_chars": len(text),
    }


@router.post("/api/workflows/{wf_id}/artifacts/custom-requirements")
async def upload_custom_requirements(
    wf_id: str, file: UploadFile = File(...)
) -> dict[str, Any]:
    workspace = await _workspace(wf_id)
    filename = Path(file.filename or "CUSTOM_REQUIREMENTS.txt").name
    raw = await file.read()
    if len(raw) > 200_000_000:
        raise HTTPException(status_code=413, detail="Requirements file is too large")
    source = _safe_path(workspace, f"user_data/{filename}")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(raw)
    try:
        content = _extract_text(filename, raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read requirements: {exc}") from exc
    output = _safe_path(workspace, "CUSTOM_REQUIREMENTS.md")
    output.write_text(content, encoding="utf-8")
    return {"status": "ok", "path": "CUSTOM_REQUIREMENTS.md", "source": f"user_data/{filename}"}


@router.put("/api/workflows/{wf_id}/artifacts/{path:path}")
async def update_artifact(wf_id: str, path: str, body: ArtifactUpdate) -> dict[str, Any]:
    workspace = await _workspace(wf_id)
    target = _safe_path(workspace, path)
    if target.suffix.lower() not in TEXT_SUFFIXES:
        raise HTTPException(status_code=415, detail="Only text artifacts can be edited")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.content, encoding="utf-8")
    return {"status": "ok", **_artifact_item(workspace, target)}


@router.get("/api/workflows/{wf_id}/artifacts/{path:path}")
async def read_artifact(
    wf_id: str,
    path: str,
    raw: bool = Query(False),
    preview: str | None = Query(None),
):
    workspace = await _workspace(wf_id)
    target = _safe_path(workspace, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    kind = _artifact_type(target)
    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    if raw:
        return FileResponse(target, media_type=media_type, filename=target.name)
    if preview == "html" and kind == "binary":
        escaped = target.name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return HTMLResponse(
            f"<!doctype html><meta charset='utf-8'><style>body{{font:14px system-ui;padding:32px;color:#333}}</style>"
            f"<h2>{escaped}</h2><p>This binary file can be downloaded from the toolbar.</p>"
        )
    if kind in {"image", "pdf", "binary"}:
        return FileResponse(target, media_type=media_type)
    text = target.read_text(encoding="utf-8", errors="replace")
    content: Any = text
    if kind == "json":
        try:
            content = json.loads(text)
        except json.JSONDecodeError:
            kind = "text"
    return {**_artifact_item(workspace, target), "content": content}
