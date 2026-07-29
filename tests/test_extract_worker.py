from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services import extract_worker


class ExtractWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        extract_worker._inflight.clear()

    async def asyncTearDown(self) -> None:
        tasks = list(extract_worker._inflight.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        extract_worker._inflight.clear()

    async def _wait_for_terminal(self, directory: Path, name: str) -> dict:
        for _ in range(200):
            entry = extract_worker.get_status(directory)["files"].get(name, {})
            if entry.get("status") in {"done", "failed"}:
                return entry
            await asyncio.sleep(0.01)
        self.fail("Extraction did not reach a terminal state")

    async def test_schedule_is_deduplicated_and_persistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.pdf").write_bytes(b"source")
            calls = 0

            def extract(source: Path, previous: Path | None):
                nonlocal calls
                calls += 1
                self.assertEqual(source.name, "sample.pdf")
                self.assertIsNone(previous)
                return "extracted text", {"kind": "pdf"}

            extract_worker.schedule_extract(root, "sample.pdf", extract)
            extract_worker.schedule_extract(root, "sample.pdf", extract)
            status = await self._wait_for_terminal(root, "sample.pdf")

            self.assertEqual(calls, 1)
            self.assertEqual(status["status"], "done")
            self.assertEqual(status["extracted_chars"], len("extracted text"))
            self.assertEqual(status["kind"], "pdf")
            extracted = root / status["extracted_path"]
            self.assertEqual(extracted.read_text(encoding="utf-8"), "extracted text")
            self.assertEqual(extract_worker.get_status(root)["version"], 1)

    async def test_failure_is_recorded_without_task_exception(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "broken.docx").write_bytes(b"broken")

            def extract(_source: Path, _previous: Path | None):
                raise ValueError("unreadable document")

            extract_worker.schedule_extract(root, "broken.docx", extract)
            status = await self._wait_for_terminal(root, "broken.docx")
            self.assertEqual(status["status"], "failed")
            self.assertIn("ValueError: unreadable document", status["error"])
            self.assertIsNone(status["extracted_path"])

    def test_pending_shape_matches_frontend_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extract_worker.mark_pending(root, "paper.pdf")
            status = extract_worker.get_status(root)
            entry = status["files"]["paper.pdf"]
            self.assertEqual(entry["status"], "pending")
            self.assertIsNone(entry["error"])
            self.assertIsNone(entry["extracted_chars"])
            self.assertIn("duration_ms", entry)


if __name__ == "__main__":
    unittest.main()
