"""Persistent, deduplicated background extraction queue for uploaded files."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

_STATUS_FILE = ".extract_status.json"
_STATUS_VERSION = 1
_GLOBAL_SEMAPHORE = asyncio.Semaphore(4)
_inflight: dict[tuple[str, str], asyncio.Task[None]] = {}
_inflight_lock = asyncio.Lock()

ExtractFn = Callable[[Path, Optional[Path]], tuple[Optional[str], dict[str, Any]]]


def _safe_name(name: str) -> str:
    if not name or "\x00" in name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("Extraction name must be a plain filename")
    return name


def _status_path(dir_: Path) -> Path:
    return Path(dir_).resolve() / _STATUS_FILE


def _empty_status() -> dict[str, Any]:
    return {"version": _STATUS_VERSION, "files": {}}


def _load_status(dir_: Path) -> dict[str, Any]:
    path = _status_path(dir_)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return _empty_status()
    if not isinstance(value, dict) or not isinstance(value.get("files"), dict):
        return _empty_status()
    value["version"] = _STATUS_VERSION
    return value


def _save_status(dir_: Path, data: dict[str, Any]) -> None:
    directory = Path(dir_).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / _STATUS_FILE
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _update_status(dir_: Path, name: str, **fields: Any) -> None:
    name = _safe_name(name)
    data = _load_status(dir_)
    entry = data["files"].get(name)
    if not isinstance(entry, dict):
        entry = {}
    entry.update(fields)
    data["files"][name] = entry
    _save_status(dir_, data)


def get_status(dir_: Path) -> dict[str, Any]:
    """Read versioned extraction status for an upload directory."""

    return _load_status(Path(dir_))


def mark_pending(dir_: Path, name: str) -> None:
    """Mark a freshly uploaded file as waiting for extraction."""

    _update_status(
        Path(dir_),
        name,
        status="pending",
        started_at=int(time.time()),
        error=None,
        extracted_path=None,
        extracted_chars=None,
        duration_ms=None,
    )


def _write_extracted_text(upload_dir: Path, name: str, content: str) -> Path:
    output = (upload_dir / f"{name}.extracted.txt").resolve()
    try:
        output.relative_to(upload_dir.resolve())
    except ValueError as exc:
        raise ValueError("Extraction output leaves the upload directory") from exc
    output.write_text(content, encoding="utf-8")
    return output


async def _run_extract(upload_dir: Path, name: str, extract_fn: ExtractFn) -> None:
    started = time.perf_counter()
    source = (upload_dir / name).resolve()
    try:
        source.relative_to(upload_dir.resolve())
    except ValueError as exc:
        raise ValueError("Extraction source leaves the upload directory") from exc
    previous = _load_status(upload_dir)["files"].get(name, {})
    prior_path: Path | None = None
    if isinstance(previous, dict) and previous.get("extracted_path"):
        candidate = (upload_dir / str(previous["extracted_path"])).resolve()
        try:
            candidate.relative_to(upload_dir.resolve())
            if candidate.is_file():
                prior_path = candidate
        except ValueError:
            prior_path = None

    _update_status(
        upload_dir,
        name,
        status="extracting",
        started_at=int(time.time()),
        error=None,
        duration_ms=None,
    )
    try:
        if not source.is_file():
            raise FileNotFoundError(source)
        async with _GLOBAL_SEMAPHORE:
            result = await asyncio.to_thread(extract_fn, source, prior_path)
            if inspect.isawaitable(result):
                result = await result
        if not isinstance(result, tuple) or len(result) != 2:
            raise TypeError("extract_fn must return (text_or_path, metadata)")
        extracted, metadata = result
        if not isinstance(metadata, dict):
            metadata = {"metadata": metadata}

        extracted_path: Path | None = None
        extracted_chars: int | None = None
        if extracted is not None:
            if not isinstance(extracted, str):
                raise TypeError("extract_fn text/path result must be a string or None")
            possible = Path(extracted)
            if possible.is_absolute() and possible.is_file():
                resolved = possible.resolve()
                try:
                    resolved.relative_to(upload_dir.resolve())
                except ValueError as exc:
                    raise ValueError("Extractor returned a path outside the upload directory") from exc
                extracted_path = resolved
                extracted_chars = len(resolved.read_text(encoding="utf-8", errors="replace"))
            else:
                extracted_path = _write_extracted_text(upload_dir, name, extracted)
                extracted_chars = len(extracted)
        if metadata.get("extracted_chars") is not None:
            try:
                extracted_chars = int(metadata["extracted_chars"])
            except (TypeError, ValueError):
                pass
        duration_ms = round((time.perf_counter() - started) * 1000)
        fields: dict[str, Any] = {
            "status": "done",
            "error": None,
            "extracted_path": extracted_path.relative_to(upload_dir).as_posix()
            if extracted_path
            else metadata.get("extracted_path"),
            "extracted_chars": extracted_chars,
            "duration_ms": duration_ms,
        }
        fields.update(
            {key: value for key, value in metadata.items() if key not in {"status", "error"}}
        )
        _update_status(upload_dir, name, **fields)
    except asyncio.CancelledError:
        _update_status(
            upload_dir,
            name,
            status="pending",
            error="Extraction cancelled",
            duration_ms=round((time.perf_counter() - started) * 1000),
        )
        raise
    except Exception as exc:
        log.exception("Extraction failed for %s", source)
        _update_status(
            upload_dir,
            name,
            status="failed",
            error=f"{type(exc).__name__}: {exc}"[:2000],
            extracted_path=None,
            extracted_chars=None,
            duration_ms=round((time.perf_counter() - started) * 1000),
        )


def schedule_extract(upload_dir: Path, name: str, extract_fn: ExtractFn) -> None:
    """Schedule one extraction and deduplicate the same directory/name pair."""

    directory = Path(upload_dir).resolve()
    name = _safe_name(name)
    if not callable(extract_fn):
        raise TypeError("extract_fn must be callable")
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as exc:
        raise RuntimeError("schedule_extract must be called from a running event loop") from exc
    key = (str(directory).casefold(), name.casefold())
    current = _inflight.get(key)
    if current and not current.done():
        return
    mark_pending(directory, name)

    async def run_and_cleanup() -> None:
        try:
            async with _inflight_lock:
                existing = _inflight.get(key)
                if existing is not None and existing is not asyncio.current_task() and not existing.done():
                    return
            await _run_extract(directory, name, extract_fn)
        finally:
            async with _inflight_lock:
                if _inflight.get(key) is asyncio.current_task():
                    _inflight.pop(key, None)

    task = loop.create_task(run_and_cleanup(), name=f"extract:{name}")
    _inflight[key] = task
