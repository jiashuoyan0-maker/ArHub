from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.routers import docx_export
from backend.routers.docx_export import DocxExportRequest
from backend.services import docx_exporter
from backend.services.docx_exporter import DocxExportError


class DocxExporterTests(unittest.IsolatedAsyncioTestCase):
    async def test_python_engine_creates_valid_arhub_docx(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "COURSE_PAPER.md"
            source.write_text(
                "# Research title\n\n正文 paragraph text.\n\n"
                "| Metric | Value |\n| --- | --- |\n| Accuracy | 0.95 |\n",
                encoding="utf-8",
            )
            result = await docx_exporter.export_markdown_to_docx(
                workspace,
                source_file="COURSE_PAPER.md",
                engine="python",
                template="course_paper",
            )

            output = Path(result["output_path"])
            self.assertTrue(output.is_file())
            self.assertEqual(result["engine"], "python")
            with zipfile.ZipFile(output) as archive:
                self.assertIn("word/document.xml", archive.namelist())
                core = archive.read("docProps/core.xml").decode("utf-8")
                self.assertIn("ArHub", core)

    async def test_auto_engine_falls_back_when_node_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "PROPOSAL.md").write_text("# Proposal\n", encoding="utf-8")
            with patch.object(docx_exporter, "_node_executable", return_value=None):
                result = await docx_exporter.export_markdown_to_docx(
                    workspace, engine="auto", template="thesis_proposal"
                )
            self.assertEqual(result["engine"], "python")
            self.assertIn("python fallback", result["log"])

    async def test_source_escape_and_unknown_engine_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            outside = Path(directory) / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            with self.assertRaises(DocxExportError):
                docx_exporter.resolve_markdown_source(workspace, "../outside.md")
            (workspace / "paper.md").write_text("inside", encoding="utf-8")
            with self.assertRaisesRegex(DocxExportError, "engine"):
                await docx_exporter.export_markdown_to_docx(
                    workspace, source_file="paper.md", engine="unsupported"
                )

    def test_request_schema_preserves_recovered_defaults(self) -> None:
        request = DocxExportRequest()
        self.assertIsNone(request.source_file)
        self.assertIsNone(request.style_profile)
        self.assertEqual(request.engine, "auto")

    async def test_response_header_encodes_non_ascii_source_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            output = workspace / "课程论文.docx"
            output.write_bytes(b"docx")
            result = {
                "output_path": str(output),
                "source_path": str(workspace / "课程论文.md"),
                "engine": "python",
            }
            with (
                patch.object(
                    docx_export,
                    "_workflow_or_404",
                    AsyncMock(return_value={"workspace_dir": str(workspace)}),
                ),
                patch.object(docx_export, "_workspace", return_value=workspace),
                patch.object(
                    docx_export,
                    "export_markdown_to_docx",
                    AsyncMock(return_value=result),
                ),
            ):
                response = await docx_export.export_docx("wf-test")

            self.assertEqual(
                response.headers["x-arhub-source"], quote("课程论文.md", safe="")
            )
            self.assertTrue(response.headers["x-arhub-source"].isascii())


if __name__ == "__main__":
    unittest.main()
