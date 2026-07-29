"""Compatibility loader for legacy DOCX tool integrations."""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

try:
    from services.docx_exporter import export_markdown_python
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.services.docx_exporter import export_markdown_python


@lru_cache(maxsize=4)
def load_docx_export(tools_dir: Path) -> Any:
    """Load an optional legacy tools/docx_export.py or return the source fallback."""

    root = Path(tools_dir).resolve()
    module_path = (root / "docx_export.py").resolve()
    try:
        module_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Invalid tools directory") from exc
    if not module_path.is_file():
        return SimpleNamespace(markdown_to_docx=export_markdown_python)
    name = f"arhub_docx_export_{abs(hash(str(module_path)))}"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_markdown_to_docx(tools_dir: Path) -> Any:
    """Return the active Markdown-to-DOCX callable."""

    module: ModuleType | SimpleNamespace = load_docx_export(Path(tools_dir))
    converter = getattr(module, "markdown_to_docx", None)
    if not callable(converter):
        raise AttributeError("DOCX export module has no markdown_to_docx function")
    return converter
