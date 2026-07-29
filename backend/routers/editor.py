"""Workspace editor API: files, previews, builds, and provider-neutral AI tools."""

from __future__ import annotations

import asyncio
import html
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Annotated, Any, AsyncIterator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

try:
    from config import (
        RUNTIME_DRAWIO,
        RUNTIME_NODE,
        RUNTIME_PYTHON,
        RUNTIME_TEXLIVE,
        TOOLS_DIR,
        WORKSPACES_DIR,
    )
    from services import editor_ai as editor_ai_service
    from services.docx_exporter import DocxExportError, export_markdown_to_docx
    from services.editor_agent import editor_agent_manager
    from services.llm_client import describe_image
    from services.state_store import get_all_settings, get_db, get_workflow
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import (
        RUNTIME_DRAWIO,
        RUNTIME_NODE,
        RUNTIME_PYTHON,
        RUNTIME_TEXLIVE,
        TOOLS_DIR,
        WORKSPACES_DIR,
    )
    from backend.services import editor_ai as editor_ai_service
    from backend.services.docx_exporter import DocxExportError, export_markdown_to_docx
    from backend.services.editor_agent import editor_agent_manager
    from backend.services.llm_client import describe_image
    from backend.services.state_store import get_all_settings, get_db, get_workflow


log = logging.getLogger(__name__)
router = APIRouter(tags=["editor"])

MAX_UPLOAD_SIZE = 100 * 1024 * 1024
MAX_TEXT_SIZE = 10 * 1024 * 1024
TEXT_SUFFIXES = {
    ".bib",
    ".cfg",
    ".csv",
    ".drawio",
    ".htm",
    ".html",
    ".ini",
    ".json",
    ".log",
    ".md",
    ".markdown",
    ".py",
    ".rst",
    ".tex",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".ps1",
    ".bat",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
MARKDOWN_MAIN_BY_TEMPLATE = {
    "thesis_proposal": "PROPOSAL.md",
    "literature_review": "LITERATURE_REVIEW.md",
    "course_paper": "COURSE_PAPER.md",
    "course_report": "COURSE_REPORT.md",
}


class SaveRequest(BaseModel):
    path: str
    content: str


class CreateFileRequest(BaseModel):
    path: str
    content: str = ""


class DrawioExportRequest(BaseModel):
    path: str


class GenerateImageRequest(BaseModel):
    prompt: str
    lang: str = "zh"
    aspect_ratio: str = "3:2"
    filename: str = ""


class AiEditRequest(BaseModel):
    message: str
    current_file: str
    current_content: str
    compile_log: str = ""
    ref_file: str = ""
    role: str = "auto"


class AiAgentRequest(BaseModel):
    message: str
    current_file: str = ""
    compile_log: str = ""


class AiAgentApplyRequest(BaseModel):
    paths: list[str]


class RunScriptRequest(BaseModel):
    path: str


async def _workflow_or_404(workflow_id: str) -> dict[str, Any]:
    db = await get_db()
    try:
        workflow = await get_workflow(db, workflow_id)
    finally:
        await db.close()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


async def _workspace_and_workflow(workflow_id: str) -> tuple[Path, dict[str, Any]]:
    workflow = await _workflow_or_404(workflow_id)
    workspace = Path(workflow.get("workspace_dir") or "").resolve()
    root = Path(WORKSPACES_DIR).resolve()
    try:
        workspace.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid workflow workspace") from exc
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace, workflow


def _safe_path(workspace: Path, supplied: str, *, allow_root: bool = False) -> Path:
    if not supplied or "\x00" in supplied:
        raise HTTPException(status_code=400, detail="A non-empty file path is required")
    path = (workspace / supplied.replace("\\", "/")).resolve()
    try:
        path.relative_to(workspace.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="File path leaves the workspace") from exc
    if path == workspace and not allow_root:
        raise HTTPException(status_code=400, detail="A file path is required")
    return path


def _relative(workspace: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace.resolve()).as_posix()


def _params(workflow: dict[str, Any]) -> dict[str, Any]:
    value = workflow.get("params")
    return value if isinstance(value, dict) else {}


def _editor_mode(workflow: dict[str, Any], workspace: Path) -> str:
    params = _params(workflow)
    explicit = str(params.get("editor_mode") or "").lower()
    output_format = str(
        params.get("output_format") or params.get("format") or params.get("output_type") or ""
    ).lower()
    if explicit in {"latex", "markdown"}:
        return explicit
    if output_format in {"docx", "word", "markdown", "md"}:
        return "markdown"
    template = str(workflow.get("template") or "")
    if template in MARKDOWN_MAIN_BY_TEMPLATE:
        return "markdown"
    markdown_candidates = [
        workspace / value for value in [*MARKDOWN_MAIN_BY_TEMPLATE.values(), "paper/main.md"]
    ]
    if any(path.is_file() for path in markdown_candidates) and not (
        workspace / "paper" / "main.tex"
    ).is_file():
        return "markdown"
    return "latex"


def _main_source(workflow: dict[str, Any], workspace: Path) -> Path:
    if _editor_mode(workflow, workspace) == "latex":
        return workspace / "paper" / "main.tex"
    template = str(workflow.get("template") or "")
    preferred = MARKDOWN_MAIN_BY_TEMPLATE.get(template, "paper/main.md")
    candidates = [
        preferred,
        "paper/main.md",
        "PROPOSAL.md",
        "LITERATURE_REVIEW.md",
        "COURSE_PAPER.md",
        "COURSE_REPORT.md",
    ]
    for relative in dict.fromkeys(candidates):
        candidate = workspace / relative
        if candidate.is_file():
            return candidate
    return workspace / preferred


def _docx_output(workflow: dict[str, Any], workspace: Path) -> Path:
    return _main_source(workflow, workspace).with_suffix(".docx")


def _pdf_output(workflow: dict[str, Any], workspace: Path) -> Path:
    source = _main_source(workflow, workspace)
    return source.with_suffix(".pdf") if source.suffix.lower() == ".tex" else workspace / "paper" / "main.pdf"


def _file_item(workspace: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(workspace).as_posix()
    parent = path.parent.relative_to(workspace).as_posix()
    return {
        "name": path.name,
        "path": relative,
        "dir": "" if parent == "." else parent,
        "type": path.suffix.lower().lstrip(".") or "file",
        "size": path.stat().st_size,
        "modified_at": path.stat().st_mtime,
    }


def _listed_files(workspace: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in workspace.rglob("*"):
        if not path.is_file() or path.is_symlink() or ".git" in path.parts:
            continue
        try:
            result.append(_file_item(workspace, path))
        except OSError:
            continue
    return sorted(result, key=lambda item: (item["dir"].lower(), item["name"].lower()))


def _find_executable(*candidates: Path | str | None) -> Path | None:
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file():
            return path
        found = shutil.which(str(candidate))
        if found:
            return Path(found)
    return None


async def _run_process(
    arguments: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = await asyncio.create_subprocess_exec(
        *arguments,
        cwd=str(cwd),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
        stderr += f"\nProcess timed out after {timeout}s".encode()
        return 124, stdout.decode("utf-8", errors="replace"), stderr.decode(
            "utf-8", errors="replace"
        )
    return (
        int(process.returncode or 0),
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
    )


def _docx_html(path: Path) -> str:
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="python-docx is unavailable") from exc

    document = Document(str(path))
    blocks: list[str] = []
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            paragraph = Paragraph(child, document)
            text = html.escape(paragraph.text).replace("\n", "<br>")
            if not text:
                blocks.append("<p>&nbsp;</p>")
                continue
            style = (paragraph.style.name if paragraph.style else "").lower()
            match = re.search(r"heading\s*(\d+)", style)
            if match:
                level = min(6, max(1, int(match.group(1))))
                blocks.append(f"<h{level}>{text}</h{level}>")
            else:
                blocks.append(f"<p>{text}</p>")
        elif child.tag.endswith("}tbl"):
            table = Table(child, document)
            rows = []
            for row in table.rows:
                cells = "".join(f"<td>{html.escape(cell.text)}</td>" for cell in row.cells)
                rows.append(f"<tr>{cells}</tr>")
            blocks.append("<table>" + "".join(rows) + "</table>")
    title = html.escape(path.name)
    body = "".join(blocks) or "<p>This document has no previewable text.</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>{title}</title><style>
body{{font-family:"Segoe UI","Microsoft YaHei",sans-serif;color:#1f2328;background:#fff;
max-width:900px;margin:0 auto;padding:36px 48px;line-height:1.75}}
h1,h2,h3,h4,h5,h6{{line-height:1.3;margin:1.2em 0 .5em}}p{{margin:.65em 0}}
table{{border-collapse:collapse;width:100%;margin:1em 0}}td{{border:1px solid #c8ccd0;padding:6px 9px}}
</style></head><body>{body}</body></html>"""


def _word_counts(text: str, *, latex: bool = False) -> dict[str, int]:
    if latex:
        text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
        text = re.sub(r"\\(?:begin|end)\{[^}]+\}", " ", text)
        text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", text)
        text = text.replace("{", " ").replace("}", " ")
    else:
        text = re.sub(r"```[\s\S]*?```", " ", text)
        text = re.sub(r"!??\[[^]]*\]\([^)]*\)", " ", text)
        text = re.sub(r"[#>*_`~-]", " ", text)
    chinese = len(re.findall(r"[\u3400-\u9fff]", text))
    english = len(re.findall(r"\b[A-Za-z]+(?:['-][A-Za-z]+)*\b", text))
    return {"chinese": chinese, "english": english, "total": chinese + english}


def _max_pages(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("max_pages", "page_limit", "pages"):
            if key in value:
                try:
                    number = int(value[key])
                    if number > 0:
                        return number
                except (TypeError, ValueError):
                    pass
        for nested in value.values():
            result = _max_pages(nested)
            if result:
                return result
    return None


def _pdf_pages(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        from PyPDF2 import PdfReader

        return len(PdfReader(str(path)).pages)
    except Exception:
        return 0


def _snapshot(workspace: Path) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for path in workspace.rglob("*"):
        if not path.is_file() or path.is_symlink() or ".git" in path.parts:
            continue
        try:
            stat = path.stat()
            result[path.relative_to(workspace).as_posix()] = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            continue
    return result


@router.get("/api/editor/{wf_id}/mode")
async def get_mode(wf_id: str) -> dict[str, str]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    source = _main_source(workflow, workspace)
    return {"mode": _editor_mode(workflow, workspace), "main_file": _relative(workspace, source)}


@router.get("/api/editor/{wf_id}/files")
async def list_files(wf_id: str) -> list[dict[str, Any]]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    return _listed_files(workspace)


@router.get("/api/editor/{wf_id}/file-preview-html")
async def file_preview_html(wf_id: str, path: str) -> HTMLResponse:
    workspace, _ = await _workspace_and_workflow(wf_id)
    target = _safe_path(workspace, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if target.suffix.lower() == ".docx":
        return HTMLResponse(_docx_html(target))
    if target.suffix.lower() in TEXT_SUFFIXES:
        content = html.escape(target.read_text(encoding="utf-8", errors="replace"))
        return HTMLResponse(f"<!doctype html><meta charset='utf-8'><pre>{content}</pre>")
    raise HTTPException(status_code=415, detail="This file type has no HTML preview")


@router.get("/api/editor/{wf_id}/file")
async def read_file(wf_id: str, path: str) -> Any:
    workspace, _ = await _workspace_and_workflow(wf_id)
    target = _safe_path(workspace, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if target.suffix.lower() in TEXT_SUFFIXES:
        if target.stat().st_size > MAX_TEXT_SIZE:
            raise HTTPException(status_code=413, detail="Text file is too large for the editor")
        return {"content": target.read_text(encoding="utf-8-sig", errors="replace")}
    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return FileResponse(str(target), media_type=media_type)


@router.put("/api/editor/{wf_id}/file")
async def save_file(wf_id: str, req: SaveRequest) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    if len(req.content.encode("utf-8")) > MAX_TEXT_SIZE:
        raise HTTPException(status_code=413, detail="Text file is too large")
    target = _safe_path(workspace, req.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    return {"ok": True, "path": _relative(workspace, target), "size": target.stat().st_size}


@router.post("/api/editor/{wf_id}/upload")
async def upload_file(
    wf_id: str,
    path: str,
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    target = _safe_path(workspace, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    temporary = target.with_name(target.name + ".arhub-upload.tmp")
    try:
        with temporary.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    raise HTTPException(status_code=413, detail="Upload exceeds 100 MB")
                output.write(chunk)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
        await file.close()
    return {"ok": True, "path": _relative(workspace, target), "size": size}


@router.post("/api/editor/{wf_id}/create-file")
async def create_file(wf_id: str, req: CreateFileRequest) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    target = _safe_path(workspace, req.path)
    if target.exists():
        raise HTTPException(status_code=409, detail="File already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    return {"ok": True, "path": _relative(workspace, target)}


@router.delete("/api/editor/{wf_id}/file")
async def delete_file(wf_id: str, path: str) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    target = _safe_path(workspace, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    target.unlink()
    return {"ok": True, "deleted": path}


@router.get("/api/editor/{wf_id}/download")
async def download_file(wf_id: str, path: str) -> FileResponse:
    workspace, _ = await _workspace_and_workflow(wf_id)
    target = _safe_path(workspace, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(target), filename=target.name)


def _drawio_executable() -> Path | None:
    return _find_executable(
        Path(RUNTIME_DRAWIO) if Path(RUNTIME_DRAWIO).is_file() else None,
        Path(RUNTIME_DRAWIO) / "draw.io.exe",
        Path(RUNTIME_DRAWIO) / "drawio.exe",
        "draw.io",
        "drawio",
    )


@router.post("/api/editor/{wf_id}/drawio-export")
async def drawio_export(wf_id: str, req: DrawioExportRequest) -> dict[str, Any]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    source = _safe_path(workspace, req.path)
    if not source.is_file() or source.suffix.lower() != ".drawio":
        raise HTTPException(status_code=404, detail="DrawIO source not found")
    executable = _drawio_executable()
    if executable is None:
        raise HTTPException(status_code=503, detail="DrawIO CLI is not available")

    pdf = source.with_suffix(".pdf")
    code, stdout, stderr = await _run_process(
        [str(executable), "--export", "--format", "pdf", "--output", str(pdf), str(source)],
        cwd=workspace,
        timeout=180,
    )
    if code or not pdf.is_file():
        raise HTTPException(status_code=500, detail=(stderr or stdout or "DrawIO export failed")[-2000:])
    mode = _editor_mode(workflow, workspace)
    png: Path | None = None
    if mode == "markdown":
        png = source.with_suffix(".png")
        code, out2, err2 = await _run_process(
            [
                str(executable),
                "--export",
                "--format",
                "png",
                "--scale",
                "3",
                "--output",
                str(png),
                str(source),
            ],
            cwd=workspace,
            timeout=180,
        )
        if code or not png.is_file():
            raise HTTPException(status_code=500, detail=(err2 or out2 or "PNG export failed")[-2000:])
    return {
        "ok": True,
        "mode": mode,
        "pdf_path": _relative(workspace, pdf),
        "png_path": _relative(workspace, png) if png else "",
        "primary_path": _relative(workspace, png or pdf),
    }


@router.get("/api/editor/{wf_id}/image-check")
async def image_check(wf_id: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    settings = await get_all_settings()
    key = settings.get("gpt_image_api_key", "").strip()
    url = settings.get("gpt_image_base_url", "").strip()
    return {"available": bool(key and url), "configured": bool(key and url)}


@router.post("/api/editor/{wf_id}/generate-image")
async def generate_image(wf_id: str, req: GenerateImageRequest) -> dict[str, Any]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    settings = await get_all_settings()
    api_key = settings.get("gpt_image_api_key", "").strip()
    base_url = settings.get("gpt_image_base_url", "").strip()
    if not api_key or not base_url:
        raise HTTPException(status_code=400, detail="Image API URL and key are not configured")
    script = Path(TOOLS_DIR) / "gpt_image.py"
    python = _find_executable(RUNTIME_PYTHON, sys.executable)
    if not script.is_file() or python is None:
        raise HTTPException(status_code=503, detail="Image generation runtime is unavailable")
    requested = Path(req.filename).name if req.filename else f"generated_{int(time.time())}.png"
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(requested).stem).strip("._") or "generated"
    output = workspace / "figures" / f"{stem}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    env = {key: str(value) for key, value in os.environ.items() if value is not None}
    env.update(
        {
            "PYTHONUTF8": "1",
            "GPT_IMAGE_API_KEY": api_key,
            "GPT_IMAGE_BASE_URL": base_url,
        }
    )
    code, stdout, stderr = await _run_process(
        [
            str(python),
            "-X",
            "utf8",
            str(script),
            "--prompt",
            req.prompt,
            "--output",
            str(output),
            "--lang",
            "en" if req.lang == "en" else "zh",
            "--aspect-ratio",
            req.aspect_ratio,
        ],
        cwd=workspace,
        timeout=360,
        env=env,
    )
    pdf = output.with_suffix(".pdf")
    if code or not output.is_file():
        raise HTTPException(status_code=502, detail=(stderr or stdout or "Image generation failed")[-3000:])
    relative_png = _relative(workspace, output)
    relative_pdf = _relative(workspace, pdf) if pdf.is_file() else relative_png
    if _editor_mode(workflow, workspace) == "markdown":
        include_code = f"![示意图]({relative_png})"
    else:
        include_code = f"\\includegraphics[width=\\textwidth]{{../{relative_pdf}}}"
    return {
        "ok": True,
        "png_path": relative_png,
        "pdf_path": relative_pdf,
        "size": output.stat().st_size,
        "include_code": include_code,
        "log": (stdout + "\n" + stderr)[-5000:],
    }


async def _compile_markdown(workspace: Path, workflow: dict[str, Any]) -> dict[str, Any]:
    source = _main_source(workflow, workspace)
    try:
        result = await export_markdown_to_docx(
            workspace,
            source_file=_relative(workspace, source),
            engine="auto",
            template=str(workflow.get("template") or ""),
        )
    except DocxExportError as exc:
        return {"success": False, "log": str(exc), "docx_path": "", "pdf_size": 0}
    output = Path(result["output_path"])
    return {
        "success": True,
        "log": str(result.get("log", ""))[-100_000:],
        "docx_path": _relative(workspace, output),
        "pdf_size": int(result.get("size") or output.stat().st_size),
        "engine": result.get("engine"),
    }


def _tex_executable(name: str) -> Path | None:
    return _find_executable(
        Path(RUNTIME_TEXLIVE) / "bin" / "windows" / f"{name}.exe",
        Path(RUNTIME_TEXLIVE) / "bin" / "win32" / f"{name}.exe",
        name,
    )


async def _compile_latex(workspace: Path, workflow: dict[str, Any]) -> dict[str, Any]:
    source = _main_source(workflow, workspace)
    if not source.is_file():
        return {"success": False, "log": f"LaTeX source not found: {_relative(workspace, source)}"}
    xelatex = _tex_executable("xelatex")
    if xelatex is None:
        return {"success": False, "log": "XeLaTeX is not available."}
    cwd = source.parent
    command = [str(xelatex), "-interaction=nonstopmode", "-halt-on-error", source.name]
    logs: list[str] = []
    code, stdout, stderr = await _run_process(command, cwd=cwd, timeout=240)
    logs.extend([stdout, stderr])
    aux = source.with_suffix(".aux")
    if code == 0 and aux.is_file() and "\\bibdata" in aux.read_text(encoding="utf-8", errors="ignore"):
        bibtex = _tex_executable("bibtex")
        if bibtex:
            bib_code, bib_out, bib_err = await _run_process(
                [str(bibtex), source.stem], cwd=cwd, timeout=180
            )
            logs.extend([bib_out, bib_err])
            if bib_code != 0:
                code = bib_code
    if code == 0:
        for _ in range(2):
            code, stdout, stderr = await _run_process(command, cwd=cwd, timeout=240)
            logs.extend([stdout, stderr])
            if code:
                break
    combined = "\n".join(logs)[-200_000:]
    compile_log = cwd / "compile.log"
    compile_log.write_text(combined, encoding="utf-8")
    output = source.with_suffix(".pdf")
    success = code == 0 and output.is_file()
    return {
        "success": success,
        "log": combined,
        "pdf_path": _relative(workspace, output) if output.is_file() else "",
        "pdf_size": output.stat().st_size if output.is_file() else 0,
    }


@router.post("/api/editor/{wf_id}/compile")
async def compile_paper(wf_id: str) -> dict[str, Any]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    if _editor_mode(workflow, workspace) == "markdown":
        return await _compile_markdown(workspace, workflow)
    return await _compile_latex(workspace, workflow)


@router.get("/api/editor/{wf_id}/pdf")
async def get_pdf(wf_id: str) -> FileResponse:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    target = _pdf_output(workflow, workspace)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="PDF has not been generated")
    return FileResponse(str(target), media_type="application/pdf")


@router.get("/api/editor/{wf_id}/docx-status")
async def docx_status(wf_id: str) -> dict[str, Any]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    target = _docx_output(workflow, workspace)
    return {
        "available": target.is_file(),
        "path": _relative(workspace, target) if target.is_file() else "",
        "size": target.stat().st_size if target.is_file() else 0,
    }


@router.get("/api/editor/{wf_id}/docx")
async def get_docx(wf_id: str) -> FileResponse:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    target = _docx_output(workflow, workspace)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="DOCX has not been generated")
    return FileResponse(
        str(target),
        filename=target.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/api/editor/{wf_id}/stats")
async def get_stats(wf_id: str, path: str = "") -> dict[str, Any]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    mode = _editor_mode(workflow, workspace)
    if path:
        target = _safe_path(workspace, path)
        if not target.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        counts = _word_counts(
            target.read_text(encoding="utf-8", errors="replace"),
            latex=target.suffix.lower() in {".tex", ".bib"},
        )
        return {"path": path, "words": counts, "total_words": counts}

    files: list[Path]
    if mode == "latex":
        paper = workspace / "paper"
        files = list(paper.rglob("*.tex")) if paper.is_dir() else []
    else:
        source = _main_source(workflow, workspace)
        files = [source] if source.is_file() else []
    aggregate = {"chinese": 0, "english": 0, "total": 0}
    for target in files:
        counts = _word_counts(
            target.read_text(encoding="utf-8", errors="replace"), latex=mode == "latex"
        )
        for key in aggregate:
            aggregate[key] += counts[key]
    pdf_pages = _pdf_pages(_pdf_output(workflow, workspace))
    if not pdf_pages and mode == "markdown" and aggregate["total"]:
        pdf_pages = max(1, (aggregate["total"] + 799) // 800)
    return {
        "total_words": aggregate,
        "pdf_pages": pdf_pages,
        "max_pages": _max_pages(_params(workflow)),
        "mode": mode,
    }


def _validated_edit_reply(workspace: Path, result: dict[str, Any]) -> dict[str, Any]:
    target = result.get("target_file")
    if isinstance(target, str) and target:
        result["target_file"] = _relative(workspace, _safe_path(workspace, target))
    edits = result.get("multi_edit")
    if isinstance(edits, list):
        normalized = []
        for item in edits:
            if not isinstance(item, dict) or not isinstance(item.get("content"), str):
                continue
            path = _relative(workspace, _safe_path(workspace, str(item.get("path", ""))))
            normalized.append({"path": path, "content": item["content"]})
        result["multi_edit"] = normalized
    return result


@router.post("/api/editor/{wf_id}/ai-edit")
async def ai_edit_endpoint(wf_id: str, req: AiEditRequest) -> dict[str, Any]:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    files = [item["path"] for item in _listed_files(workspace)]
    extra_context = ""
    if req.ref_file:
        candidates = [workspace / req.ref_file]
        candidates.extend(path for path in workspace.rglob("*") if path.is_file() and path.name == Path(req.ref_file).name)
        for candidate in candidates:
            try:
                candidate = _safe_path(workspace, _relative(workspace, candidate))
            except (HTTPException, ValueError):
                continue
            if candidate.is_file() and candidate.stat().st_size <= MAX_TEXT_SIZE:
                extra_context = candidate.read_text(encoding="utf-8", errors="replace")
                break
    role = req.role
    if role == "auto":
        suffix = Path(req.current_file).suffix.lower()
        role = "python" if suffix == ".py" else "markdown" if suffix in {".md", ".markdown"} else _editor_mode(workflow, workspace)
    history = editor_agent_manager.get_history(wf_id)
    try:
        result = await editor_ai_service.ai_edit(
            req.message,
            req.current_file,
            req.current_content,
            files,
            req.compile_log,
            extra_context,
            history,
            role,
        )
        result = _validated_edit_reply(workspace, result)
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Editor AI failed for %s", wf_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    editor_agent_manager.append_history(wf_id, "user", req.message)
    editor_agent_manager.append_history(wf_id, "ai", str(result.get("summary") or "Edit prepared"))
    return result


async def _sse_events(queue: asyncio.Queue[dict[str, Any] | None]) -> AsyncIterator[str]:
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=15)
        except asyncio.TimeoutError:
            yield ": keep-alive\n\n"
            continue
        if event is None:
            break
        yield "data: " + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n\n"


@router.post("/api/editor/{wf_id}/ai-agent")
async def ai_agent_endpoint(wf_id: str, req: AiAgentRequest) -> StreamingResponse:
    workspace, workflow = await _workspace_and_workflow(wf_id)
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Agent instruction is empty")
    try:
        run = await editor_agent_manager.start(
            wf_id,
            workspace,
            req.message.strip(),
            mode=_editor_mode(workflow, workspace),
            current_file=req.current_file,
            compile_log=req.compile_log,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return StreamingResponse(
        _sse_events(run.queue),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/editor/{wf_id}/ai-agent-apply")
async def ai_agent_apply(wf_id: str, req: AiAgentApplyRequest) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    try:
        return editor_agent_manager.apply(wf_id, workspace, req.paths)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/editor/{wf_id}/ai-agent-discard")
async def ai_agent_discard(wf_id: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    try:
        return editor_agent_manager.discard(wf_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/editor/{wf_id}/ai-agent-undo")
async def ai_agent_undo(wf_id: str) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    return editor_agent_manager.undo(wf_id, workspace)


@router.post("/api/editor/{wf_id}/ai-agent-stop")
async def ai_agent_stop(wf_id: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    stopped = editor_agent_manager.stop(wf_id)
    return {"ok": True, "stopped": stopped}


@router.get("/api/editor/{wf_id}/ai-agent-check")
async def ai_agent_check(wf_id: str, log_offset: int = 0) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    return editor_agent_manager.check(wf_id, workspace, log_offset)


@router.post("/api/editor/{wf_id}/run-script")
async def run_script(wf_id: str, req: RunScriptRequest) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    script = _safe_path(workspace, req.path)
    if not script.is_file() or script.suffix.lower() != ".py":
        raise HTTPException(status_code=400, detail="A Python script inside the workspace is required")
    python = _find_executable(RUNTIME_PYTHON, sys.executable)
    if python is None:
        raise HTTPException(status_code=503, detail="Python runtime is unavailable")
    before = _snapshot(workspace)
    env = {key: str(value) for key, value in os.environ.items() if value is not None}
    env.update({"PYTHONUTF8": "1", "MPLBACKEND": "Agg"})
    started = time.perf_counter()
    code, stdout, stderr = await _run_process(
        [str(python), "-X", "utf8", str(script)], cwd=workspace, timeout=300, env=env
    )
    duration_ms = round((time.perf_counter() - started) * 1000)
    after = _snapshot(workspace)
    changed = sorted(path for path, metadata in after.items() if before.get(path) != metadata)
    return {
        "stdout": stdout[-200_000:],
        "stderr": stderr[-200_000:],
        "exit_code": code,
        "duration_ms": duration_ms,
        "changed_files": changed,
    }


@router.post("/api/editor/{wf_id}/describe-image")
async def describe_image_endpoint(wf_id: str, path: str) -> dict[str, Any]:
    workspace, _ = await _workspace_and_workflow(wf_id)
    source = _safe_path(workspace, path)
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    temporary: tempfile.TemporaryDirectory[str] | None = None
    image = source
    try:
        if source.suffix.lower() == ".pdf":
            try:
                import fitz
            except ImportError as exc:
                raise HTTPException(status_code=503, detail="PDF image support is unavailable") from exc
            temporary = tempfile.TemporaryDirectory()
            image = Path(temporary.name) / "page.png"
            document = fitz.open(str(source))
            try:
                if not document.page_count:
                    raise HTTPException(status_code=400, detail="PDF has no pages")
                document[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(str(image))
            finally:
                document.close()
        elif source.suffix.lower() not in IMAGE_SUFFIXES:
            raise HTTPException(status_code=415, detail="Unsupported image type")
        description = await describe_image(str(image), "Describe this research asset accurately.")
        return {"ok": True, "description": description}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        if temporary:
            temporary.cleanup()


@router.get("/api/editor/{wf_id}/chat-history")
async def get_chat_history(wf_id: str) -> list[dict[str, Any]]:
    await _workflow_or_404(wf_id)
    return editor_agent_manager.get_history(wf_id)


@router.delete("/api/editor/{wf_id}/chat-history")
async def clear_chat_history(wf_id: str) -> dict[str, Any]:
    await _workflow_or_404(wf_id)
    editor_agent_manager.clear_history(wf_id)
    return {"ok": True}
