"""Portable workflow Markdown-to-DOCX export endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

try:
    from config import WORKSPACES_DIR
    from services.docx_exporter import DocxExportError, export_markdown_to_docx
    from services.state_store import get_db, get_workflow
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import WORKSPACES_DIR
    from backend.services.docx_exporter import DocxExportError, export_markdown_to_docx
    from backend.services.state_store import get_db, get_workflow


router = APIRouter(tags=["exports"])


class DocxExportRequest(BaseModel):
    source_file: str | None = Field(
        default=None,
        description="Workspace-relative Markdown source. Auto-detected when omitted.",
    )
    style_profile: str | None = Field(
        default=None,
        description="Profile filename under tools/docx_style_profiles.",
    )
    engine: str | None = Field(
        default="auto",
        description="auto, python (python-docx), or node (docx.js with math support).",
    )


async def _workflow_or_404(workflow_id: str) -> dict[str, Any]:
    db = await get_db()
    try:
        workflow = await get_workflow(db, workflow_id)
    finally:
        await db.close()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


def _workspace(workflow: dict[str, Any]) -> Path:
    workspace = Path(workflow.get("workspace_dir") or "").resolve()
    root = Path(WORKSPACES_DIR).resolve()
    try:
        workspace.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid workflow workspace") from exc
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@router.post("/api/workflows/{wf_id}/export-docx")
async def export_docx(
    wf_id: str, body: DocxExportRequest = DocxExportRequest()
) -> FileResponse:
    """Export a workflow Markdown artifact as a formatted DOCX download."""

    workflow = await _workflow_or_404(wf_id)
    workspace = _workspace(workflow)
    try:
        result = await export_markdown_to_docx(
            workspace,
            source_file=body.source_file,
            style_profile=body.style_profile,
            engine=body.engine,
            template=str(workflow.get("template") or ""),
        )
    except DocxExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"DOCX export failed: {type(exc).__name__}: {exc}"
        ) from exc
    output = Path(result["output_path"])
    return FileResponse(
        str(output),
        filename=output.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "X-ArHub-Export-Engine": str(result.get("engine", "")),
            "X-ArHub-Source": quote(Path(result["source_path"]).name, safe=""),
        },
    )
